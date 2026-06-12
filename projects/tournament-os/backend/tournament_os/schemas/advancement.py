from tournament_os.schemas.common import ApiModel


class AdvancementRead(ApiModel):
    stage_id: str
    advanced_count: int
    eliminated_count: int
    advanced_registration_ids: list[str]


class NextStageAssignmentRead(ApiModel):
    source_stage_id: str
    target_stage_id: str
    assigned_count: int
    target_group_ids: list[str]


class WinnerRead(ApiModel):
    stage_id: str
    registration_id: str
    display_name: str
    total_points: int
