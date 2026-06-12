from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tournament_os.database import Base
from tournament_os.domain.enums import (
    CheckInSessionStatus,
    CheckInStatus,
    DisputeStatus,
    RegistrationStatus,
    RoundStatus,
    ScoreStatus,
    StageStatus,
)
from tournament_os.models.base import IdMixin, TimestampMixin


class Registration(IdMixin, TimestampMixin, Base):
    __tablename__ = "registrations"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"))
    status: Mapped[str] = mapped_column(String(40), default=RegistrationStatus.SUBMITTED.value)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    in_game_name: Mapped[str] = mapped_column(String(120), nullable=False)
    game_uid: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_method: Mapped[str] = mapped_column(String(60), nullable=False)
    contact_value: Mapped[str] = mapped_column(String(255), nullable=False)
    review_note: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_registration_tournament_user"),
        UniqueConstraint("tournament_id", "game_uid", name="uq_registration_tournament_game_uid"),
        Index("ix_registrations_tournament_status", "tournament_id", "status"),
        Index("ix_registrations_tournament_user", "tournament_id", "user_id"),
        Index("ix_registrations_tournament_game_uid", "tournament_id", "game_uid"),
    )


class Team(IdMixin, TimestampMixin, Base):
    __tablename__ = "teams"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    captain_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(40), default="draft")


class TeamMember(IdMixin, Base):
    __tablename__ = "team_members"

    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    in_game_name: Mapped[str] = mapped_column(String(120), nullable=False)
    game_uid: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(60), default="member")


class Stage(IdMixin, TimestampMixin, Base):
    __tablename__ = "stages"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=StageStatus.DRAFT.value)

    __table_args__ = (
        UniqueConstraint("tournament_id", "sequence", name="uq_stages_tournament_sequence"),
        Index("ix_stages_tournament_sequence", "tournament_id", "sequence"),
        Index("ix_stages_tournament_status", "tournament_id", "status"),
    )


class Group(IdMixin, TimestampMixin, Base):
    __tablename__ = "groups"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    stage_id: Mapped[str] = mapped_column(ForeignKey("stages.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("stage_id", "sequence", name="uq_groups_stage_sequence"),
        Index("ix_groups_stage_sequence", "stage_id", "sequence"),
    )


class GroupParticipant(IdMixin, TimestampMixin, Base):
    __tablename__ = "group_participants"

    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), nullable=False)
    registration_id: Mapped[str] = mapped_column(ForeignKey("registrations.id"), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default="assigned")

    __table_args__ = (
        UniqueConstraint("group_id", "registration_id", name="uq_group_participant"),
        Index("ix_group_participants_group_status", "group_id", "status"),
        Index("ix_group_participants_registration", "registration_id"),
    )


class Round(IdMixin, TimestampMixin, Base):
    __tablename__ = "rounds"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    stage_id: Mapped[str] = mapped_column(ForeignKey("stages.id"), nullable=False)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default=RoundStatus.SCHEDULED.value)

    __table_args__ = (
        UniqueConstraint("group_id", "sequence", name="uq_rounds_group_sequence"),
        Index("ix_rounds_group_sequence", "group_id", "sequence"),
        Index("ix_rounds_tournament_status", "tournament_id", "status"),
    )


class CheckInSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "check_in_sessions"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    stage_id: Mapped[str] = mapped_column(ForeignKey("stages.id"), nullable=False)
    group_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id"))
    round_id: Mapped[str | None] = mapped_column(ForeignKey("rounds.id"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    session_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=CheckInSessionStatus.DRAFT.value)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        Index("ix_check_in_sessions_tournament_status", "tournament_id", "status"),
        Index("ix_check_in_sessions_stage_opens", "stage_id", "opens_at"),
    )


class CheckIn(IdMixin, TimestampMixin, Base):
    __tablename__ = "check_ins"

    check_in_session_id: Mapped[str] = mapped_column(ForeignKey("check_in_sessions.id"), nullable=False)
    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    registration_id: Mapped[str] = mapped_column(ForeignKey("registrations.id"), nullable=False)
    group_participant_id: Mapped[str | None] = mapped_column(ForeignKey("group_participants.id"))
    status: Mapped[str] = mapped_column(String(40), default=CheckInStatus.PENDING.value)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_in_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(40), default="web")
    note: Mapped[str | None] = mapped_column(String(500))
    replaced_by_registration_id: Mapped[str | None] = mapped_column(ForeignKey("registrations.id"))

    __table_args__ = (
        UniqueConstraint("check_in_session_id", "registration_id", name="uq_check_in_session_registration"),
        Index("ix_check_ins_session_status", "check_in_session_id", "status"),
        Index("ix_check_ins_registration_status", "registration_id", "status"),
    )


class Score(IdMixin, TimestampMixin, Base):
    __tablename__ = "scores"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    stage_id: Mapped[str] = mapped_column(ForeignKey("stages.id"), nullable=False)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), nullable=False)
    round_id: Mapped[str] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    registration_id: Mapped[str] = mapped_column(ForeignKey("registrations.id"), nullable=False)
    placement: Mapped[int] = mapped_column(Integer, nullable=False)
    placement_points: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)
    penalty_points: Mapped[int] = mapped_column(Integer, default=0)
    bye_points: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=ScoreStatus.DRAFT.value)
    evidence_uri: Mapped[str | None] = mapped_column(String(1000))
    note: Mapped[str | None] = mapped_column(String(500))
    submitted_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    approved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    formula_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("round_id", "registration_id", name="uq_scores_round_registration"),
        Index("ix_scores_tournament_stage_status", "tournament_id", "stage_id", "status"),
        Index("ix_scores_round_registration", "round_id", "registration_id"),
        Index("ix_scores_registration_status", "registration_id", "status"),
    )


class Dispute(IdMixin, TimestampMixin, Base):
    __tablename__ = "disputes"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    score_id: Mapped[str] = mapped_column(ForeignKey("scores.id"), nullable=False)
    registration_id: Mapped[str] = mapped_column(ForeignKey("registrations.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=DisputeStatus.OPEN.value)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence_uri: Mapped[str | None] = mapped_column(String(1000))
    resolved_note: Mapped[str | None] = mapped_column(String(1000))
    opened_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    resolved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        Index("ix_disputes_tournament_status", "tournament_id", "status"),
        Index("ix_disputes_registration_status", "registration_id", "status"),
        Index("ix_disputes_score", "score_id"),
    )
