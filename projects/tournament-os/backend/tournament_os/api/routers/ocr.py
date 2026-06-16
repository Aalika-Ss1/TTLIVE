import hashlib
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.ocr import OcrService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.database import get_session
from tournament_os.models.competition import Score
from tournament_os.models.evidence import Attachment, OcrSuggestion
from tournament_os.schemas.ocr import AttachmentRead, OcrSuggestionRead
from tournament_os.schemas.scoring import ScoreCreateItem

router = APIRouter(prefix="/admin", tags=["ocr"])


@router.post("/scores/{score_id}/evidence", response_model=list[OcrSuggestionRead])
async def upload_evidence(
    score_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> list[OcrSuggestion]:
    # Verify the score exists
    score = session.get(Score, score_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found",
        )

    # Read contents and calculate checksum
    contents = await file.read()
    checksum = hashlib.sha256(contents).hexdigest()

    # Check for duplicate file uploads
    existing_attachment = session.scalar(
        select(Attachment).where(Attachment.checksum == checksum)
    )
    if existing_attachment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate evidence file already uploaded",
        )

    # Save file to a local project uploads directory
    uploads_dir = Path(__file__).resolve().parents[3] / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    attachment_id = str(uuid.uuid4())
    file_extension = Path(file.filename or "evidence.png").suffix
    file_path = uploads_dir / f"{attachment_id}{file_extension}"
    file_path.write_bytes(contents)

    # Save Attachment record
    attachment = Attachment(
        id=attachment_id,
        filename=file.filename or "evidence.png",
        file_path=str(file_path),
        checksum=checksum,
        file_size=len(contents),
    )
    session.add(attachment)
    session.flush()

    # Run OCR Pipeline processing
    ocr_service = OcrService(session)
    suggestions = ocr_service.process_screenshot(attachment.id, score_id)
    session.commit()

    return suggestions


@router.get("/ocr/suggestions", response_model=list[OcrSuggestionRead])
def get_pending_suggestions(
    session: Session = Depends(get_session),
) -> list[OcrSuggestion]:
    suggestions = session.scalars(
        select(OcrSuggestion).where(OcrSuggestion.status == "pending")
    ).all()
    return list(suggestions)


@router.post("/ocr/suggestions/{suggestion_id}/accept", response_model=OcrSuggestionRead)
def accept_suggestion(
    suggestion_id: str,
    session: Session = Depends(get_session),
) -> OcrSuggestion:
    # Find suggestion
    suggestion = session.get(OcrSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR Suggestion not found",
        )

    if suggestion.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OCR Suggestion is not pending",
        )

    # Find the linked score
    if not suggestion.score_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OCR Suggestion has no linked score",
        )

    score = session.get(Score, suggestion.score_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked score not found",
        )

    attachment = session.get(Attachment, suggestion.attachment_id)
    evidence_uri = attachment.file_path if attachment else None

    # Call ScoreEntryService to correct/update the score
    score_service = ScoreEntryService(session)
    payload = ScoreCreateItem(
        registration_id=score.registration_id,
        placement=suggestion.detected_placement or 1,
        bonus_points=score.bonus_points,
        penalty_points=score.penalty_points,
        penalty_reason=None,
        evidence_uri=evidence_uri,
    )
    score_service.correct_score(
        score_id=score.id,
        payload=payload,
        actor_user_id=None,
        reason="OCR suggestion accepted",
    )

    # Mark suggestion as accepted
    suggestion.status = "accepted"
    session.commit()

    return suggestion


@router.post("/ocr/suggestions/{suggestion_id}/reject", response_model=OcrSuggestionRead)
def reject_suggestion(
    suggestion_id: str,
    session: Session = Depends(get_session),
) -> OcrSuggestion:
    # Find suggestion
    suggestion = session.get(OcrSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR Suggestion not found",
        )

    if suggestion.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OCR Suggestion is not pending",
        )

    # Mark suggestion as rejected
    suggestion.status = "rejected"
    session.commit()

    return suggestion
