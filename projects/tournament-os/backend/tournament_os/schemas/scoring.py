from pydantic import Field

from tournament_os.schemas.common import ApiModel


class ScoreCreateItem(ApiModel):
    registration_id: str
    placement: int = Field(ge=1)
    bonus_points: int = 0
    penalty_points: int = 0
    penalty_reason: str | None = None
    evidence_uri: str | None = None


class ScoreCreate(ApiModel):
    scores: list[ScoreCreateItem]


class ScoreRead(ApiModel):
    id: str
    registration_id: str
    placement: int
    placement_points: int
    bonus_points: int
    penalty_points: int
    bye_points: int
    total_points: int
    status: str
    evidence_uri: str | None = None


class PublicLeaderboardEntry(ApiModel):
    rank: int
    display_name: str
    group_name: str | None = None
    total_points: int
    games_played: int
