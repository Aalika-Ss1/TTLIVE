from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tournament_os.database import Base
from tournament_os.models.base import IdMixin, TimestampMixin


class Attachment(IdMixin, TimestampMixin, Base):
    __tablename__ = "attachments"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    suggestions: Mapped[list["OcrSuggestion"]] = relationship(
        "OcrSuggestion",
        back_populates="attachment",
        cascade="all, delete-orphan",
    )


class OcrSuggestion(IdMixin, TimestampMixin, Base):
    __tablename__ = "ocr_suggestions"

    attachment_id: Mapped[str] = mapped_column(ForeignKey("attachments.id"), nullable=False, index=True)
    score_id: Mapped[str | None] = mapped_column(ForeignKey("scores.id"), nullable=True, index=True)
    player_name_raw: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detected_placement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attachment: Mapped["Attachment"] = relationship("Attachment", back_populates="suggestions")
