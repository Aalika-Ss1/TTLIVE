from datetime import datetime
from tournament_os.schemas.common import ApiModel


class AttachmentRead(ApiModel):
    id: str
    filename: str
    file_path: str
    checksum: str
    file_size: int
    created_at: datetime
    updated_at: datetime


class OcrSuggestionRead(ApiModel):
    id: str
    attachment_id: str
    score_id: str | None = None
    player_name_raw: str | None = None
    detected_placement: int | None = None
    confidence_score: float
    raw_ocr_text: str | None = None
    status: str
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
