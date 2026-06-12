from tournament_os.domain.enums import (
    AdvancementType,
    LobbyAssignmentType,
    ParticipantType,
    ScoreResetPolicy,
    TournamentModel,
    TournamentStatus,
)
from tournament_os.domain.errors import DomainError
from tournament_os.models.tournament import RuleSet, ScoreFormulaModel, Tournament
from tournament_os.schemas.tournament import RuleSetCreate, RuleSetValidationResult
from sqlalchemy.orm import Session


SUPPORTED_PHASE_1_MODELS = {
    TournamentModel.FIXED_POINTS.value,
    TournamentModel.GROUP_POINTS_QUALIFIER.value,
}


def validate_rule_set(rule_set: RuleSetCreate) -> RuleSetValidationResult:
    errors: list[str] = []

    if rule_set.model not in SUPPORTED_PHASE_1_MODELS:
        errors.append("Phase 1 supports fixed_points and group_points_qualifier only.")

    if rule_set.participant_type != ParticipantType.SOLO.value:
        errors.append("Phase 1 MVP is solo-only.")

    if rule_set.lobby_size <= 0:
        errors.append("Lobby size must be positive.")

    if rule_set.max_participants < rule_set.min_participants:
        errors.append("Max participants cannot be lower than min participants.")

    if rule_set.max_participants > 64:
        errors.append("MVP code path supports up to 64 participants.")

    if rule_set.score_reset_policy != ScoreResetPolicy.RESET_EACH_STAGE.value:
        errors.append("Phase 1 default requires reset_each_stage.")

    advancement_type = rule_set.advancement_policy_json.get("type")
    if advancement_type != AdvancementType.TOP_N_PER_LOBBY.value:
        errors.append("Phase 1 default advancement is top_n_per_lobby.")

    top_n = rule_set.advancement_policy_json.get("top_n")
    if not isinstance(top_n, int) or top_n <= 0:
        errors.append("Advancement policy requires a positive integer top_n.")
    elif top_n > rule_set.lobby_size:
        errors.append("Advancement top_n cannot be greater than lobby size.")

    lobby_assignment_type = rule_set.lobby_assignment_policy_json.get("type")
    if lobby_assignment_type not in {
        LobbyAssignmentType.RANDOM.value,
        LobbyAssignmentType.MANUAL.value,
    }:
        errors.append("Phase 1 lobby assignment must be random or manual.")

    for placement in range(1, rule_set.lobby_size + 1):
        if placement not in rule_set.placement_points_json:
            errors.append(f"Placement points missing for placement {placement}.")

    return RuleSetValidationResult(valid=not errors, errors=errors)


class RuleSetService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_rule_set(self, tournament_id: str, payload: RuleSetCreate) -> tuple[RuleSet, ScoreFormulaModel]:
        validation = validate_rule_set(payload)
        if not validation.valid:
            raise DomainError("rule_set_invalid", "Rule set is invalid.")

        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        if tournament.status != TournamentStatus.DRAFT.value:
            raise DomainError("tournament_not_editable", "Rule sets can be edited only while tournament is draft.")

        rule_set = RuleSet(
            tournament_id=tournament_id,
            name=payload.name,
            model=payload.model,
            participant_type=payload.participant_type,
            lobby_size=payload.lobby_size,
            max_participants=payload.max_participants,
            min_participants=payload.min_participants,
            games_per_stage=payload.games_per_stage,
            final_games=payload.final_games,
            score_reset_policy=payload.score_reset_policy,
            advancement_policy_json=payload.advancement_policy_json,
            lobby_assignment_policy_json=payload.lobby_assignment_policy_json,
            verification_policy_json=payload.verification_policy_json,
        )
        self.session.add(rule_set)
        self.session.flush()

        formula = ScoreFormulaModel(
            tournament_id=tournament_id,
            rule_set_id=rule_set.id,
            name=f"{payload.name} Formula",
            placement_points_json={str(k): v for k, v in payload.placement_points_json.items()},
            bonus_rules_json={"enabled": False},
            penalty_rules_json={"requires_reason": True},
            bye_rule_json={"behavior": "advance_only", "default_points": 0},
            tie_break_order_json=[
                "total_points",
                "first_place_count",
                "average_placement",
                "latest_game_points",
                "latest_game_placement",
                "admin_decision",
            ],
        )
        self.session.add(formula)
        self.session.flush()

        tournament.active_rule_set_id = rule_set.id
        tournament.active_score_formula_id = formula.id
        self.session.flush()
        return rule_set, formula

    def lock_rule_set(self, tournament_id: str, actor_user_id: str | None = None) -> RuleSet:
        from datetime import datetime, timezone
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        
        rule_set = self.session.get(RuleSet, tournament.active_rule_set_id)
        if not rule_set:
            raise DomainError("rule_set_not_found", "Active rule set not found.")
            
        formula = self.session.get(ScoreFormulaModel, tournament.active_score_formula_id)
        if not formula:
            raise DomainError("score_formula_not_found", "Active score formula not found.")

        now = datetime.now(timezone.utc)
        rule_set.status = "locked"
        rule_set.locked_at = now
        rule_set.locked_by_user_id = actor_user_id
        # In a real app we serialize the config to config_snapshot_json, here we just save a simple snapshot
        rule_set.config_snapshot_json = {"locked": True, "model": rule_set.model}
        
        formula.status = "locked"
        formula.locked_at = now
        formula.locked_by_user_id = actor_user_id
        
        self.session.flush()
        return rule_set
