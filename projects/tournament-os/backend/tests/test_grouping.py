import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.application.grouping import stage_group_counts
from tournament_os.domain.errors import DomainError


class GroupingTests(unittest.TestCase):
    def test_sixteen_player_shape(self) -> None:
        self.assertEqual(
            stage_group_counts(16, 8),
            [("Round 1", 2, 2), ("Final", 1, 3)],
        )

    def test_thirty_two_player_shape(self) -> None:
        self.assertEqual(
            stage_group_counts(32, 8),
            [("Round 1", 4, 2), ("Semi Final", 2, 2), ("Final", 1, 3)],
        )

    def test_rejects_more_than_sixty_four_players(self) -> None:
        with self.assertRaises(DomainError) as context:
            stage_group_counts(65, 8)

        self.assertEqual(context.exception.code, "participant_count_unsupported")


if __name__ == "__main__":
    unittest.main()
