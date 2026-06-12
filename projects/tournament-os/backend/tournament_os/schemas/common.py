from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(ApiModel):
    error: dict[str, object]


class MutationEvent(ApiModel):
    name: str
    entity_type: str
    entity_id: str


class MutationResult(ApiModel):
    data: dict[str, object]
    events: list[MutationEvent] = []
