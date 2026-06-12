import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.domain.enums import RegistrationStatus, ScoreStatus, TournamentStatus
from tournament_os.domain.errors import DomainError
from tournament_os.domain.state_transitions import (
    ensure_registration_transition,
    ensure_score_transition,
    ensure_tournament_transition,
)


class StateTransitionTests(unittest.TestCase):
    def test_tournament_can_move_from_draft_to_registration_open(self) -> None:
        ensure_tournament_transition(
            TournamentStatus.DRAFT,
            TournamentStatus.REGISTRATION_OPEN,
        )

    def test_tournament_cannot_skip_from_draft_to_live(self) -> None:
        with self.assertRaises(DomainError) as context:
            ensure_tournament_transition(TournamentStatus.DRAFT, TournamentStatus.LIVE)

        self.assertEqual(context.exception.code, "invalid_state_transition")

    def test_registration_waitlist_can_be_promoted_to_approved(self) -> None:
        ensure_registration_transition(
            RegistrationStatus.WAITLISTED,
            RegistrationStatus.APPROVED,
        )

    def test_rejected_registration_is_terminal(self) -> None:
        with self.assertRaises(DomainError):
            ensure_registration_transition(
                RegistrationStatus.REJECTED,
                RegistrationStatus.APPROVED,
            )

    def test_final_score_is_terminal_for_normal_flow(self) -> None:
        with self.assertRaises(DomainError):
            ensure_score_transition(ScoreStatus.FINAL, ScoreStatus.CORRECTED)


if __name__ == "__main__":
    unittest.main()
