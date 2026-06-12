from sqlalchemy import JSON, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from tournament_os.database import Base
from tournament_os.models.base import IdMixin, TimestampMixin


class OverlayConfig(IdMixin, TimestampMixin, Base):
    __tablename__ = "overlay_configs"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), unique=True, nullable=False, index=True)
    active_scene: Mapped[str] = mapped_column(String(120), default="leaderboard")
    emergency_mode: Mapped[bool] = mapped_column(default=False)
    emergency_message: Mapped[str | None] = mapped_column(String(500))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
