import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tournament_os.application.disputes import DisputeService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.database import Base
from tournament_os.domain.enums import DisputeStatus, ScoreStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import Registration
from tournament_os.models.identity import User
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.scoring import ScoreCreateItem


class DisputeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.now = datetime.now(timezone.utc)
        
        self.admin = User(id="admin_1", display_name="Admin", role="tournament_admin")
        self.player = User(id="player_1", display_name="Player", role="player")
        self.session.add_all([self.admin, self.player])
        self.session.flush()

        self.tournament = Tournament(
            id="t_1",
            created_by_user_id=self.admin.id,
            name="Dispute Test",
            game="Test",
            participant_type="solo",
            max_participants=8,
            registration_open_at=self.now,
            registration_close_at=self.now + timedelta(days=1),
            status="registration_open",
            public_slug="dispute-test",
        )
        self.session.add(self.tournament)
        self.session.flush()

        self.formula = ScoreFormulaModel(
            id="f_1",
            tournament_id=self.tournament.id,
            name="Test Formula",
            placement_points_json={"1": 10, "2": 5},
            bonus_rules_json={"enabled": True},
            bye_rule_json={"default_points": 0},
        )
        self.session.add(self.formula)
        self.session.flush()

        self.tournament.active_score_formula_id = self.formula.id
        self.session.flush()

        self.registration = Registration(
            id="reg_1",
            tournament_id=self.tournament.id,
            user_id=self.player.id,
            game_uid="PID_1",
            display_name="Player1",
            in_game_name="Player1",
            contact_method="discord",
            contact_value="player1#1234",
            status="approved",
        )
        self.session.add(self.registration)
        self.session.flush()

        self.scoring_service = ScoreEntryService(self.session)
        self.dispute_service = DisputeService(self.session)
        
        # Create an initial APPROVED score to dispute
        self.score = self.scoring_service.create_score(
            self.tournament.id,
            "stage_1",
            "group_1",
            "round_1",
            ScoreCreateItem(registration_id=self.registration.id, placement=2),
        )
        self.scoring_service.submit_score(self.score.id, self.player.id)
        self.scoring_service.verify_score(self.score.id, self.admin.id)
        self.scoring_service.approve_score(self.score.id, self.admin.id)
        self.assertEqual(self.score.status, ScoreStatus.APPROVED.value)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_open_dispute(self) -> None:
        dispute = self.dispute_service.open_dispute(
            self.score.id,
            self.registration.id,
            "I should be 1st place",
            opened_by_user_id=self.player.id,
        )
        self.assertEqual(dispute.status, DisputeStatus.OPEN.value)
        self.assertEqual(self.score.status, ScoreStatus.DISPUTED.value)

    def test_accept_dispute_with_correction(self) -> None:
        dispute = self.dispute_service.open_dispute(
            self.score.id,
            self.registration.id,
            "I should be 1st place",
            opened_by_user_id=self.player.id,
        )

        corrected = ScoreCreateItem(
            registration_id=self.registration.id,
            placement=1,
            bonus_points=2
        )
        
        resolved = self.dispute_service.resolve_dispute(
            dispute.id,
            DisputeStatus.ACCEPTED,
            resolved_by_user_id=self.admin.id,
            corrected_score=corrected,
        )
        
        self.assertEqual(resolved.status, DisputeStatus.ACCEPTED.value)
        
        # Score should be CORRECTED and recalculated (10 points for 1st + 2 bonus = 12)
        self.assertEqual(self.score.status, ScoreStatus.CORRECTED.value)
        self.assertEqual(self.score.placement, 1)
        self.assertEqual(self.score.total_points, 12)

    def test_accept_dispute_without_correction_raises_error(self) -> None:
        dispute = self.dispute_service.open_dispute(
            self.score.id,
            self.registration.id,
            "I should be 1st place",
            opened_by_user_id=self.player.id,
        )

        with self.assertRaises(DomainError) as context:
            self.dispute_service.resolve_dispute(
                dispute.id,
                DisputeStatus.ACCEPTED,
                resolved_by_user_id=self.admin.id,
            )
        self.assertEqual(context.exception.code, "missing_corrected_score")
        
    def test_reject_dispute(self) -> None:
        dispute = self.dispute_service.open_dispute(
            self.score.id,
            self.registration.id,
            "I should be 1st place",
            opened_by_user_id=self.player.id,
        )

        resolved = self.dispute_service.resolve_dispute(
            dispute.id,
            DisputeStatus.REJECTED,
            resolved_by_user_id=self.admin.id,
        )
        self.assertEqual(resolved.status, DisputeStatus.REJECTED.value)
        # Note: Depending on business rules, score might revert to APPROVED or stay DISPUTED.
        # Currently, the code leaves the score as DISPUTED. 
        self.assertEqual(self.score.status, ScoreStatus.DISPUTED.value)

if __name__ == "__main__":
    unittest.main()
