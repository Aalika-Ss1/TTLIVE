from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tournament_os.database import Base
from tournament_os.models.base import IdMixin, TimestampMixin


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    tournament_id: Mapped[str | None] = mapped_column(ForeignKey("tournaments.id"))
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_audit_logs_tournament_created", "tournament_id", "created_at"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id", "created_at"),
        Index("ix_audit_logs_actor_created", "actor_user_id", "created_at"),
    )


class EventOutbox(IdMixin, Base):
    __tablename__ = "event_outbox"

    tournament_id: Mapped[str | None] = mapped_column(ForeignKey("tournaments.id"))
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_event_outbox_status_created", "status", "created_at"),
        Index("ix_event_outbox_tournament_created", "tournament_id", "created_at"),
    )


class TournamentDashboardSummary(IdMixin, Base):
    __tablename__ = "tournament_dashboard_summaries"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    registration_counts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    current_stage_id: Mapped[str | None] = mapped_column(ForeignKey("stages.id"))
    current_check_in_session_id: Mapped[str | None] = mapped_column(ForeignKey("check_in_sessions.id"))
    current_check_in_counts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    pending_score_count: Mapped[int] = mapped_column(Integer, default=0)
    open_dispute_count: Mapped[int] = mapped_column(Integer, default=0)
    discord_delivery_status_json: Mapped[dict] = mapped_column(JSON, default=dict)
    next_action: Mapped[str | None] = mapped_column(String(80))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LeaderboardSnapshot(IdMixin, Base):
    __tablename__ = "leaderboard_snapshots"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    stage_id: Mapped[str | None] = mapped_column(ForeignKey("stages.id"))
    group_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id"))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    visibility: Mapped[str] = mapped_column(String(40), default="public")
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_from_score_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_leaderboard_snapshots_lookup", "tournament_id", "stage_id", "group_id", "version"),
    )


class PlayerStatusSnapshot(IdMixin, Base):
    __tablename__ = "player_status_snapshots"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    registration_id: Mapped[str | None] = mapped_column(ForeignKey("registrations.id"))
    registration_status: Mapped[str | None] = mapped_column(String(40))
    current_stage_id: Mapped[str | None] = mapped_column(ForeignKey("stages.id"))
    current_group_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id"))
    current_check_in_session_id: Mapped[str | None] = mapped_column(ForeignKey("check_in_sessions.id"))
    check_in_status: Mapped[str | None] = mapped_column(String(40))
    latest_score_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed_actions_json: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_player_status_tournament_user"),
        Index("ix_player_status_tournament_user", "tournament_id", "user_id"),
        Index("ix_player_status_registration", "registration_id"),
    )


class PublicTournamentSummary(IdMixin, Base):
    __tablename__ = "public_tournament_summaries"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    public_slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    display_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DiscordMessageJob(IdMixin, Base):
    __tablename__ = "discord_message_jobs"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    event_outbox_id: Mapped[str | None] = mapped_column(ForeignKey("event_outbox.id"))
    target_channel_id: Mapped[str] = mapped_column(String(120), nullable=False)
    message_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(String(1000))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_discord_message_jobs_status_retry", "status", "next_retry_at"),
        Index("ix_discord_message_jobs_tournament_created", "tournament_id", "created_at"),
    )
