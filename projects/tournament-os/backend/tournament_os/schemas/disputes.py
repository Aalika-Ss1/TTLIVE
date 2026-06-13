from tournament_os.schemas.common import ApiModel
from tournament_os.schemas.scoring import ScoreCreateItem


class DisputeCreate(ApiModel):
    registration_id: str
    reason: str
    opened_by_user_id: str
    evidence_uri: str | None = None


class DisputeResolve(ApiModel):
    resolved_by_user_id: str | None = None
    resolved_note: str | None = None
    corrected_score: ScoreCreateItem | None = None


class DisputeRead(ApiModel):
    id: str
    tournament_id: str
    score_id: str
    registration_id: str
    status: str
    reason: str
    evidence_uri: str | None = None
    resolved_note: str | None = None
