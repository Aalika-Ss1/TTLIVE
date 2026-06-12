import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.domain.errors import DomainError
from tournament_os.domain.scoring import (
    DEFAULT_GOLDEN_SPATULA_PLACEMENT_POINTS,
    ScoreFormula,
    ScoreInput,
    calculate_score,
)


class ScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.formula = ScoreFormula(DEFAULT_GOLDEN_SPATULA_PLACEMENT_POINTS)

    def test_calculates_default_golden_spatula_points(self) -> None:
        result = calculate_score(ScoreInput(placement=1), self.formula)

        self.assertEqual(result.placement_points, 10)
        self.assertEqual(result.total_points, 10)
        self.assertEqual(result.formula_snapshot["placement_points"][1], 10)

    def test_penalty_requires_reason(self) -> None:
        with self.assertRaises(DomainError) as context:
            calculate_score(ScoreInput(placement=2, penalty_points=1), self.formula)

        self.assertEqual(context.exception.code, "penalty_reason_required")

    def test_bonus_points_are_disabled_by_default(self) -> None:
        with self.assertRaises(DomainError) as context:
            calculate_score(ScoreInput(placement=2, bonus_points=1), self.formula)

        self.assertEqual(context.exception.code, "bonus_disabled")

    def test_rejects_placement_missing_from_locked_formula(self) -> None:
        with self.assertRaises(DomainError) as context:
            calculate_score(ScoreInput(placement=9), self.formula)

        self.assertEqual(context.exception.code, "placement_not_in_formula")


if __name__ == "__main__":
    unittest.main()
