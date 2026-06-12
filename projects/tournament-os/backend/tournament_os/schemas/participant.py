from pydantic import BaseModel, ConfigDict
from typing import Optional

class ParticipantBase(BaseModel):
    in_game_name: str
    team_name: Optional[str] = None

class ParticipantPublic(ParticipantBase):
    """ข้อมูลที่ปลอดภัยสำหรับการแสดงผลบน Stream/OBS"""
    id: int
    current_score: int = 0
    rank: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ParticipantPrivate(ParticipantPublic):
    """ข้อมูลสำหรับการจัดการหลังบ้าน (Admin Only)"""
    real_name: str
    phone_number: str
    email: Optional[str] = None
    discord_id: Optional[str] = None
    id_card_last_4: Optional[str] = None  # สำหรับการตรวจสอบตัวตน

class ParticipantCreate(ParticipantBase):
    real_name: str
    phone_number: str
    email: Optional[str] = None