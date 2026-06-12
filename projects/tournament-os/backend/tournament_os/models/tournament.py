from datetime import datetime
from sqlalchemy import JSON, DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from tournament_os.database import Base
from tournament_os.models.base import IdMixin, TimestampMixin

class Tournament(IdMixin, TimestampMixin, Base):
    __tablename__ = "tournaments"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    game: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    participant_type: Mapped[str] = mapped_column(String(40), default="solo")
    max_participants: Mapped[int] = mapped_column(Integer, default=16)
    registration_open_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registration_close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    public_slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    active_rule_set_id: Mapped[str | None] = mapped_column(String(36))
    active_score_formula_id: Mapped[str | None] = mapped_column(String(36))
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

class RuleSet(IdMixin, TimestampMixin, Base):
    __tablename__ = "rule_sets"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    source_preset_id: Mapped[str | None] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    model: Mapped[str] = mapped_column(String(40), nullable=False)
    participant_type: Mapped[str] = mapped_column(String(40), default="solo")
    lobby_size: Mapped[int] = mapped_column(Integer, default=8)
    max_participants: Mapped[int] = mapped_column(Integer, default=16)
    min_participants: Mapped[int] = mapped_column(Integer, default=8)
    games_per_stage: Mapped[int] = mapped_column(Integer, default=2)
    final_games: Mapped[int] = mapped_column(Integer, default=3)
    score_reset_policy: Mapped[str] = mapped_column(String(40), default="reset_each_stage")
    advancement_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    lobby_assignment_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    verification_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    config_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)

class ScoreFormulaModel(IdMixin, TimestampMixin, Base):
    __tablename__ = "score_formulas"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    rule_set_id: Mapped[str | None] = mapped_column(ForeignKey("rule_sets.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    placement_points_json: Mapped[dict] = mapped_column(JSON, default=dict)
    bonus_rules_json: Mapped[dict] = mapped_column(JSON, default=dict)
    penalty_rules_json: Mapped[dict] = mapped_column(JSON, default=dict)
    bye_rule_json: Mapped[dict] = mapped_column(JSON, default=dict)
    tie_break_order_json: Mapped[list] = mapped_column(JSON, default=list)
    manual_override_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    config_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)