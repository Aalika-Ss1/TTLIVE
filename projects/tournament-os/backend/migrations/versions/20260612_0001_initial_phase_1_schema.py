"""initial phase 1 schema

Revision ID: 20260612_0001
Revises:
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260612_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def id_column() -> sa.Column:
    return sa.Column("id", sa.String(length=36), primary_key=True)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    jsonb = postgresql.JSONB

    op.create_table(
        "users",
        id_column(),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("discord_id", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=40), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("discord_id"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_discord_id", "users", ["discord_id"])

    op.create_table(
        "rule_presets",
        id_column(),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("game", sa.String(length=120), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("participant_type", sa.String(length=40), nullable=False),
        sa.Column("config_json", jsonb, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
    )

    op.create_table(
        "tournaments",
        id_column(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("game", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("participant_type", sa.String(length=40), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("registration_open_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registration_close_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("public_slug", sa.String(length=160), nullable=False),
        sa.Column("active_rule_set_id", sa.String(length=36), nullable=True),
        sa.Column("active_score_formula_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("public_slug"),
    )
    op.create_index("ix_tournaments_status", "tournaments", ["status"])
    op.create_index("ix_tournaments_public_slug", "tournaments", ["public_slug"])

    op.create_table(
        "overlay_configs",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("active_scene", sa.String(length=120), nullable=False),
        sa.Column("emergency_mode", sa.Boolean(), nullable=False),
        sa.Column("emergency_message", sa.String(length=500), nullable=True),
        sa.Column("config_json", jsonb, nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("tournament_id"),
    )
    op.create_index("ix_overlay_configs_tournament_id", "overlay_configs", ["tournament_id"])

    op.create_table(
        "user_identities",
        id_column(),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_user_id", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_user_identities_provider_user"),
    )

    op.create_table(
        "tournament_user_roles",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("tournament_id", "user_id", "role", name="uq_tournament_user_roles_scope"),
    )
    op.create_index("ix_tournament_user_roles_user", "tournament_user_roles", ["tournament_id", "user_id"])
    op.create_index("ix_tournament_user_roles_role", "tournament_user_roles", ["tournament_id", "role"])

    op.create_table(
        "rule_sets",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("source_preset_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("participant_type", sa.String(length=40), nullable=False),
        sa.Column("lobby_size", sa.Integer(), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("min_participants", sa.Integer(), nullable=False),
        sa.Column("games_per_stage", sa.Integer(), nullable=False),
        sa.Column("final_games", sa.Integer(), nullable=False),
        sa.Column("score_reset_policy", sa.String(length=40), nullable=False),
        sa.Column("advancement_policy_json", jsonb, nullable=False),
        sa.Column("lobby_assignment_policy_json", jsonb, nullable=False),
        sa.Column("verification_policy_json", jsonb, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("config_snapshot_json", jsonb, nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["locked_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_preset_id"], ["rule_presets.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_rule_sets_tournament_status", "rule_sets", ["tournament_id", "status"])
    op.create_index("ix_rule_sets_source_preset", "rule_sets", ["source_preset_id"])

    op.create_table(
        "score_formulas",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("rule_set_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("placement_points_json", jsonb, nullable=False),
        sa.Column("bonus_rules_json", jsonb, nullable=False),
        sa.Column("penalty_rules_json", jsonb, nullable=False),
        sa.Column("bye_rule_json", jsonb, nullable=False),
        sa.Column("tie_break_order_json", jsonb, nullable=False),
        sa.Column("manual_override_policy_json", jsonb, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("config_snapshot_json", jsonb, nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["locked_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["rule_set_id"], ["rule_sets.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_score_formulas_tournament_status", "score_formulas", ["tournament_id", "status"])

    op.create_foreign_key("fk_tournaments_active_rule_set", "tournaments", "rule_sets", ["active_rule_set_id"], ["id"])
    op.create_foreign_key("fk_tournaments_active_score_formula", "tournaments", "score_formulas", ["active_score_formula_id"], ["id"])

    op.create_table(
        "score_formula_placement_points",
        id_column(),
        sa.Column("score_formula_id", sa.String(length=36), nullable=False),
        sa.Column("placement", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["score_formula_id"], ["score_formulas.id"]),
        sa.UniqueConstraint("score_formula_id", "placement", name="uq_formula_placement"),
    )
    op.create_index("ix_formula_placement_points_lookup", "score_formula_placement_points", ["score_formula_id", "placement"])

    op.create_table(
        "teams",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("captain_user_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["captain_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )

    op.create_table(
        "registrations",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("team_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("in_game_name", sa.String(length=120), nullable=False),
        sa.Column("game_uid", sa.String(length=120), nullable=False),
        sa.Column("contact_method", sa.String(length=60), nullable=False),
        sa.Column("contact_value", sa.String(length=255), nullable=False),
        sa.Column("review_note", sa.String(length=500), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("tournament_id", "user_id", name="uq_registration_tournament_user"),
        sa.UniqueConstraint("tournament_id", "game_uid", name="uq_registration_tournament_game_uid"),
    )
    op.create_index("ix_registrations_tournament_status", "registrations", ["tournament_id", "status"])
    op.create_index("ix_registrations_tournament_user", "registrations", ["tournament_id", "user_id"])
    op.create_index("ix_registrations_tournament_game_uid", "registrations", ["tournament_id", "game_uid"])

    op.create_table(
        "team_members",
        id_column(),
        sa.Column("team_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("in_game_name", sa.String(length=120), nullable=False),
        sa.Column("game_uid", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=60), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "stages",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("format", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("tournament_id", "sequence", name="uq_stages_tournament_sequence"),
    )
    op.create_index("ix_stages_tournament_sequence", "stages", ["tournament_id", "sequence"])
    op.create_index("ix_stages_tournament_status", "stages", ["tournament_id", "status"])

    op.create_table(
        "groups",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("stage_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("stage_id", "sequence", name="uq_groups_stage_sequence"),
    )
    op.create_index("ix_groups_stage_sequence", "groups", ["stage_id", "sequence"])

    op.create_table(
        "group_participants",
        id_column(),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("registration_id", sa.String(length=36), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"]),
        sa.UniqueConstraint("group_id", "registration_id", name="uq_group_participant"),
    )
    op.create_index("ix_group_participants_group_status", "group_participants", ["group_id", "status"])
    op.create_index("ix_group_participants_registration", "group_participants", ["registration_id"])

    op.create_table(
        "rounds",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("stage_id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("group_id", "sequence", name="uq_rounds_group_sequence"),
    )
    op.create_index("ix_rounds_group_sequence", "rounds", ["group_id", "sequence"])
    op.create_index("ix_rounds_tournament_status", "rounds", ["tournament_id", "status"])

    op.create_table(
        "check_in_sessions",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("stage_id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=36), nullable=True),
        sa.Column("round_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("session_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("opens_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closes_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_check_in_sessions_tournament_status", "check_in_sessions", ["tournament_id", "status"])
    op.create_index("ix_check_in_sessions_stage_opens", "check_in_sessions", ["stage_id", "opens_at"])

    op.create_table(
        "check_ins",
        id_column(),
        sa.Column("check_in_session_id", sa.String(length=36), nullable=False),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("registration_id", sa.String(length=36), nullable=False),
        sa.Column("group_participant_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("replaced_by_registration_id", sa.String(length=36), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["check_in_session_id"], ["check_in_sessions.id"]),
        sa.ForeignKeyConstraint(["checked_in_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["group_participant_id"], ["group_participants.id"]),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"]),
        sa.ForeignKeyConstraint(["replaced_by_registration_id"], ["registrations.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("check_in_session_id", "registration_id", name="uq_check_in_session_registration"),
    )
    op.create_index("ix_check_ins_session_status", "check_ins", ["check_in_session_id", "status"])
    op.create_index("ix_check_ins_registration_status", "check_ins", ["registration_id", "status"])

    op.create_table(
        "scores",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("stage_id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("round_id", sa.String(length=36), nullable=False),
        sa.Column("registration_id", sa.String(length=36), nullable=False),
        sa.Column("placement", sa.Integer(), nullable=False),
        sa.Column("placement_points", sa.Integer(), nullable=False),
        sa.Column("bonus_points", sa.Integer(), nullable=False),
        sa.Column("penalty_points", sa.Integer(), nullable=False),
        sa.Column("bye_points", sa.Integer(), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("evidence_uri", sa.String(length=1000), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("submitted_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("approved_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("formula_snapshot_json", jsonb, nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"]),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("round_id", "registration_id", name="uq_scores_round_registration"),
    )
    op.create_index("ix_scores_tournament_stage_status", "scores", ["tournament_id", "stage_id", "status"])
    op.create_index("ix_scores_round_registration", "scores", ["round_id", "registration_id"])
    op.create_index("ix_scores_registration_status", "scores", ["registration_id", "status"])

    op.create_table(
        "disputes",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("score_id", sa.String(length=36), nullable=False),
        sa.Column("registration_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("evidence_uri", sa.String(length=1000), nullable=True),
        sa.Column("resolved_note", sa.String(length=1000), nullable=True),
        sa.Column("opened_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("resolved_by_user_id", sa.String(length=36), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"]),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["score_id"], ["scores.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_disputes_tournament_status", "disputes", ["tournament_id", "status"])
    op.create_index("ix_disputes_registration_status", "disputes", ["registration_id", "status"])
    op.create_index("ix_disputes_score", "disputes", ["score_id"])

    op.create_table(
        "audit_logs",
        id_column(),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("tournament_id", sa.String(length=36), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("before_json", jsonb, nullable=True),
        sa.Column("after_json", jsonb, nullable=True),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_audit_logs_tournament_created", "audit_logs", ["tournament_id", "created_at"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id", "created_at"])
    op.create_index("ix_audit_logs_actor_created", "audit_logs", ["actor_user_id", "created_at"])

    op.create_table(
        "event_outbox",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=True),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=False),
        sa.Column("payload_json", jsonb, nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_event_outbox_status_created", "event_outbox", ["status", "created_at"])
    op.create_index("ix_event_outbox_tournament_created", "event_outbox", ["tournament_id", "created_at"])

    op.create_table(
        "tournament_dashboard_summaries",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("registration_counts_json", jsonb, nullable=False),
        sa.Column("current_stage_id", sa.String(length=36), nullable=True),
        sa.Column("current_check_in_session_id", sa.String(length=36), nullable=True),
        sa.Column("current_check_in_counts_json", jsonb, nullable=False),
        sa.Column("pending_score_count", sa.Integer(), nullable=False),
        sa.Column("open_dispute_count", sa.Integer(), nullable=False),
        sa.Column("discord_delivery_status_json", jsonb, nullable=False),
        sa.Column("next_action", sa.String(length=80), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["current_check_in_session_id"], ["check_in_sessions.id"]),
        sa.ForeignKeyConstraint(["current_stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("tournament_id"),
    )

    op.create_table(
        "leaderboard_snapshots",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("stage_id", sa.String(length=36), nullable=True),
        sa.Column("group_id", sa.String(length=36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.String(length=40), nullable=False),
        sa.Column("snapshot_json", jsonb, nullable=False),
        sa.Column("generated_from_score_version", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
    )
    op.create_index("ix_leaderboard_snapshots_lookup", "leaderboard_snapshots", ["tournament_id", "stage_id", "group_id", "version"])

    op.create_table(
        "player_status_snapshots",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("registration_id", sa.String(length=36), nullable=True),
        sa.Column("registration_status", sa.String(length=40), nullable=True),
        sa.Column("current_stage_id", sa.String(length=36), nullable=True),
        sa.Column("current_group_id", sa.String(length=36), nullable=True),
        sa.Column("current_check_in_session_id", sa.String(length=36), nullable=True),
        sa.Column("check_in_status", sa.String(length=40), nullable=True),
        sa.Column("latest_score_summary_json", jsonb, nullable=False),
        sa.Column("allowed_actions_json", jsonb, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["current_check_in_session_id"], ["check_in_sessions.id"]),
        sa.ForeignKeyConstraint(["current_group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["current_stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("tournament_id", "user_id", name="uq_player_status_tournament_user"),
    )
    op.create_index("ix_player_status_tournament_user", "player_status_snapshots", ["tournament_id", "user_id"])
    op.create_index("ix_player_status_registration", "player_status_snapshots", ["registration_id"])

    op.create_table(
        "public_tournament_summaries",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("public_slug", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("display_json", jsonb, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("public_slug"),
    )

    op.create_table(
        "discord_message_jobs",
        id_column(),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("event_outbox_id", sa.String(length=36), nullable=True),
        sa.Column("target_channel_id", sa.String(length=120), nullable=False),
        sa.Column("message_type", sa.String(length=80), nullable=False),
        sa.Column("payload_json", jsonb, nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_outbox_id"], ["event_outbox.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_discord_message_jobs_status_retry", "discord_message_jobs", ["status", "next_retry_at"])
    op.create_index("ix_discord_message_jobs_tournament_created", "discord_message_jobs", ["tournament_id", "created_at"])


def downgrade() -> None:
    for table_name in [
        "discord_message_jobs",
        "public_tournament_summaries",
        "player_status_snapshots",
        "leaderboard_snapshots",
        "tournament_dashboard_summaries",
        "event_outbox",
        "audit_logs",
        "disputes",
        "scores",
        "check_ins",
        "check_in_sessions",
        "rounds",
        "group_participants",
        "groups",
        "stages",
        "team_members",
        "registrations",
        "teams",
        "score_formula_placement_points",
        "score_formulas",
        "rule_sets",
        "tournament_user_roles",
        "user_identities",
        "overlay_configs",
        "tournaments",
        "rule_presets",
        "users",
    ]:
        op.drop_table(table_name)
