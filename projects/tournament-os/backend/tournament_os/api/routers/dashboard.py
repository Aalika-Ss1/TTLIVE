from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.audit import AuditQueryService
from tournament_os.application.dashboard import DashboardQueryService
from tournament_os.database import get_session

router = APIRouter(prefix="/admin", tags=["dashboard"])


@router.get("/tournaments/{tournament_id}/dashboard")
def admin_dashboard(
    tournament_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    return DashboardQueryService(session).admin_dashboard(tournament_id)


@router.get("/tournaments/{tournament_id}/audit-logs")
def audit_logs(
    tournament_id: str,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[dict[str, object]]:
    return AuditQueryService(session).audit_logs(tournament_id, limit)


@router.get("/tournaments/{tournament_id}/events")
def event_outbox(
    tournament_id: str,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[dict[str, object]]:
    return AuditQueryService(session).event_outbox(tournament_id, limit)
