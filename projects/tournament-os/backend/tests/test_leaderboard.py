import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.domain.enums import ScoreStatus
from tournament_os.domain.leaderboard import ScoreRecord, build_leaderboard


class LeaderboardTests(unittest.TestCase):
    def test_uses_only_approved_and_final_scores(self) -> None:
        entries = build_leaderboard(
            [
                ScoreRecord("a", "Player A", 1, 1, 10, ScoreStatus.APPROVED),
                ScoreRecord("b", "Player B", 1, 1, 99, ScoreStatus.PENDING_VERIFICATION),
                ScoreRecord("c", "Player C", 1, 2, 8, ScoreStatus.FINAL),
            ]
        )

        self.assertEqual([entry.display_name for entry in entries], ["Player A", "Player C"])

    def test_tie_breaks_use_first_places_then_average_then_latest_game(self) -> None:
        entries = build_leaderboard(
            [
                ScoreRecord("a", "Player A", 1, 1, 10, ScoreStatus.APPROVED),
                ScoreRecord("a", "Player A", 2, 5, 4, ScoreStatus.APPROVED),
                ScoreRecord("b", "Player B", 1, 2, 8, ScoreStatus.APPROVED),
                ScoreRecord("b", "Player B", 2, 3, 6, ScoreStatus.APPROVED),
            ]
        )

        self.assertEqual(entries[0].display_name, "Player A")
        self.assertEqual(entries[0].rank, 1)
        self.assertEqual(entries[1].rank, 2)


if __name__ == "__main__":
    unittest.main()
