from datetime import datetime

from tournament_os.schemas.common import ApiModel


class CheckInRead(ApiModel):
    id: str
    check_in_session_id: str
    tournament_id: str
    registration_id: str
    status: str
    checked_in_at: datetime | None = None
    source: str


class CheckInRequest(ApiModel):
    registration_id: str
    source: str = "web"
