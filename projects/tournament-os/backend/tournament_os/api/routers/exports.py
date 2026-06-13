from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.exports import ExportService
from tournament_os.database import get_session
from tournament_os.domain.errors import DomainError
from tournament_os.models.tournament import Tournament

router = APIRouter(tags=["exports"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/admin/tournaments/{tournament_id}/exports/leaderboard.xlsx")
def export_leaderboard_xlsx(tournament_id: str, session: Session = Depends(get_session)) -> Response:
    tournament = session.scalar(select(Tournament).where(Tournament.id == tournament_id))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")

    xlsx_content = ExportService(session).export_leaderboard_xlsx(tournament_id)

    return Response(
        content=xlsx_content,
        headers={"Content-Disposition": f'attachment; filename="leaderboard_{tournament_id}.xlsx"'},
        media_type=XLSX_MEDIA_TYPE,
    )


@router.get("/exports/tournaments/{tournament_id}/leaderboard.csv", response_class=PlainTextResponse)
def export_leaderboard(tournament_id: str, session: Session = Depends(get_session)) -> PlainTextResponse:
    tournament = session.scalar(select(Tournament).where(Tournament.id == tournament_id))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")
        
    csv_content = ExportService(session).export_leaderboard_csv(tournament_id)
    
    return PlainTextResponse(
        content=csv_content,
        headers={"Content-Disposition": f'attachment; filename="leaderboard_{tournament_id}.csv"'},
        media_type="text/csv"
    )
