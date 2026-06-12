import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.application.rules import validate_rule_set
from tournament_os.schemas.tournament import RuleSetCreate


class RuleValidationTests(unittest.TestCase):
    def test_accepts_default_mvp_rule_set(self) -> None:
        result = validate_rule_set(
            RuleSetCreate(name="Golden Spatula 16", max_participants=16)
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_rejects_team_rule_set_for_phase_1(self) -> None:
        result = validate_rule_set(
            RuleSetCreate(
                name="Team Event",
                participant_type="team",
                max_participants=16,
            )
        )

        self.assertFalse(result.valid)
        self.assertIn("Phase 1 MVP is solo-only.", result.errors)

    def test_rejects_top_n_greater_than_lobby_size(self) -> None:
        result = validate_rule_set(
            RuleSetCreate(
                name="Bad Advance",
                max_participants=16,
                advancement_policy_json={"type": "top_n_per_lobby", "top_n": 9},
            )
        )

        self.assertFalse(result.valid)
        self.assertIn("Advancement top_n cannot be greater than lobby size.", result.errors)


if __name__ == "__main__":
    unittest.main()
