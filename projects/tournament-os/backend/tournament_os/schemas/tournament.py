from datetime import datetime

from pydantic import Field

from tournament_os.schemas.common import ApiModel


class TournamentCreate(ApiModel):
    name: str
    game: str = "Golden Spatula"
    participant_type: str = "solo"
    max_participants: int = Field(ge=2, le=64)
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    public_slug: str


class TournamentRead(ApiModel):
    id: str
    name: str
    game: str
    status: str
    participant_type: str
    max_participants: int
    public_slug: str


class RuleSetCreate(ApiModel):
    name: str
    model: str = "group_points_qualifier"
    participant_type: str = "solo"
    lobby_size: int = 8
    max_participants: int = Field(ge=2, le=64)
    min_participants: int = Field(ge=2, default=8)
    games_per_stage: int = 2
    final_games: int = 3
    score_reset_policy: str = "reset_each_stage"
    advancement_policy_json: dict[str, object] = Field(default_factory=lambda: {"type": "top_n_per_lobby", "top_n": 4})
    lobby_assignment_policy_json: dict[str, object] = Field(default_factory=lambda: {"type": "random"})
    verification_policy_json: dict[str, object] = Field(default_factory=lambda: {"manual_approval_required": True})
    placement_points_json: dict[int, int] = Field(
        default_factory=lambda: {1: 10, 2: 8, 3: 7, 4: 6, 5: 4, 6: 3, 7: 2, 8: 1}
    )


class RuleSetValidationResult(ApiModel):
    valid: bool
    errors: list[str] = []
