from typing import Dict, Any
from tournament_os.domain.errors import DomainError

DEFAULT_GOLDEN_SPATULA_PLACEMENT_POINTS = {1: 10, 2: 8, 3: 7, 4: 6, 5: 4, 6: 3, 7: 2, 8: 1}

class ScoreFormula:
    def __init__(
        self,
        placement_points: Dict[int, int],
        bonus_enabled: bool = False,
        bye_points_default: int = 0,
    ) -> None:
        self.placement_points = placement_points
        self.bonus_enabled = bonus_enabled
        self.bye_points_default = bye_points_default

class ScoreInput:
    def __init__(
        self,
        placement: int,
        bonus_points: int = 0,
        penalty_points: int = 0,
        penalty_reason: str | None = None,
        is_bye: bool = False,
    ) -> None:
        self.placement = placement
        self.bonus_points = bonus_points
        self.penalty_points = penalty_points
        self.penalty_reason = penalty_reason
        self.is_bye = is_bye

class ScoreResult:
    def __init__(
        self,
        placement: int,
        placement_points: int,
        bonus_points: int,
        penalty_points: int,
        bye_points: int,
        total_points: int,
        formula_snapshot: Dict[str, Any],
    ) -> None:
        self.placement = placement
        self.placement_points = placement_points
        self.bonus_points = bonus_points
        self.penalty_points = penalty_points
        self.bye_points = bye_points
        self.total_points = total_points
        self.formula_snapshot = formula_snapshot

def calculate_score(score_input: ScoreInput, formula: ScoreFormula) -> ScoreResult:
    # 1. Penalty validation
    if score_input.penalty_points > 0 and (score_input.penalty_reason is None or score_input.penalty_reason.strip() == ""):
        raise DomainError("penalty_reason_required", "Penalty reason is required when penalty points are non-zero.")

    # 2. Bonus validation
    if score_input.bonus_points > 0 and not formula.bonus_enabled:
        raise DomainError("bonus_disabled", "Bonus points are disabled in this formula configuration.")

    # 3. Bye vs Normal score calculation
    if score_input.is_bye:
        placement_points = 0
        bye_points = formula.bye_points_default
    else:
        if score_input.placement == 0:
            placement_points = 0
            bye_points = 0
        else:
            if score_input.placement not in formula.placement_points:
                raise DomainError("placement_not_in_formula", f"Placement {score_input.placement} is not defined in the active formula.")
            placement_points = formula.placement_points[score_input.placement]
            bye_points = 0

    total_points = placement_points + score_input.bonus_points + bye_points - score_input.penalty_points

    formula_snapshot = {
        "placement_points": formula.placement_points,
        "bonus_enabled": formula.bonus_enabled,
        "bye_points_default": formula.bye_points_default,
    }

    return ScoreResult(
        placement=score_input.placement,
        placement_points=placement_points,
        bonus_points=score_input.bonus_points,
        penalty_points=score_input.penalty_points,
        bye_points=bye_points,
        total_points=total_points,
        formula_snapshot=formula_snapshot,
    )