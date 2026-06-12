from tournament_os.schemas.common import ApiModel


class GenerateGroupsRequest(ApiModel):
    strategy: str = "random"
    create_check_in_sessions: bool = True


class GenerateGroupsResult(ApiModel):
    stages_created: int
    groups_created: int
    rounds_created: int
    participants_assigned: int
    check_in_sessions_created: int
