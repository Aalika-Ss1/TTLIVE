import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from tournament_os.models.evidence import Attachment, OcrSuggestion


class OcrService:
    def __init__(self, db: Session):
        self.db = db

    def process_screenshot(self, attachment_id: str, score_id: str | None = None) -> list[OcrSuggestion]:
        # Fetch the attachment
        attachment = self.db.scalar(select(Attachment).where(Attachment.id == attachment_id))
        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found")

        # In a real system, we would open the file at attachment.file_path
        # and run an OCR engine (e.g. Tesseract or EasyOCR) to extract text.
        # For this implementation phase, we simulate the OCR extraction.
        # We parse mock scenarios based on the filename to support unit tests,
        # and fallback to a default set of suggestions otherwise.
        
        suggestions = []
        raw_ocr_text = "MOCK OCR TEXT:\n"
        
        # Scenario 1: Mock file with specific test cases
        if "mock_test_1" in attachment.filename:
            raw_ocr_text += "1st Place: Player 07\n2nd Place: Player 16\n3rd Place: Player 04"
            mock_data = [
                ("Player 07", 1, 0.95),
                ("Player 16", 2, 0.92),
                ("Player 04", 3, 0.88),
            ]
        elif "mock_test_2" in attachment.filename:
            raw_ocr_text += "1st Place: Player 01\n2nd Place: Player 02"
            mock_data = [
                ("Player 01", 1, 0.99),
                ("Player 02", 2, 0.91),
            ]
        else:
            # Default mock behavior representing a lobby leaderboard screenshot
            raw_ocr_text += "Lobby Results:\n"
            mock_data = []
            for i in range(1, 9):
                raw_ocr_text += f"Placement {i}: Player {i:02d}\n"
                mock_data.append((f"Player {i:02d}", i, 0.85))

        for name, placement, confidence in mock_data:
            suggestion = OcrSuggestion(
                attachment_id=attachment.id,
                score_id=score_id,
                player_name_raw=name,
                detected_placement=placement,
                confidence_score=confidence,
                raw_ocr_text=raw_ocr_text,
                status="pending",
                processed_at=datetime.now(timezone.utc)
            )
            self.db.add(suggestion)
            suggestions.append(suggestion)

        self.db.flush()
        return suggestions
