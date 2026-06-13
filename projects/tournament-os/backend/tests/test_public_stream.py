import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.database import Base
from tournament_os.domain.enums import ScoreStatus
from tournament_os.models.competition import Group, Registration, Round, Stage
from tournament_os.models.identity import User
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.scoring import ScoreCreateItem


class PublicStreamTests(unittest.TestCase):
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
            name="Public Test",
            game="Test",
            participant_type="solo",
            max_participants=8,
            registration_open_at=self.now,
            registration_close_at=self.now + timedelta(days=1),
            status="registration_open",
            public_slug="public-test",
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
            contact_value="secret#1234",
            status="approved",
        )
        self.session.add(self.registration)
        self.session.flush()

        self.stage = Stage(id="stage_1", tournament_id=self.tournament.id, name="Finals", sequence=1, format="swiss", status="live")
        self.group = Group(id="group_1", tournament_id=self.tournament.id, stage_id=self.stage.id, name="Lobby A", sequence=1)
        self.round = Round(id="round_1", tournament_id=self.tournament.id, stage_id=self.stage.id, group_id=self.group.id, name="Game 1", sequence=1, status="scoring")
        self.session.add_all([self.stage, self.group, self.round])
        self.session.flush()

        self.scoring_service = ScoreEntryService(self.session)
        self.leaderboard_service = LeaderboardQueryService(self.session)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_leaderboard_excludes_private_fields(self) -> None:
        score = self.scoring_service.create_score(
            self.tournament.id,
            self.stage.id,
            self.group.id,
            self.round.id,
            ScoreCreateItem(registration_id=self.registration.id, placement=1),
        )
        self.scoring_service.submit_score(score.id, self.player.id)
        self.scoring_service.verify_score(score.id, self.admin.id)
        self.scoring_service.approve_score(score.id, self.admin.id)
        
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 1)
        entry = results[0]
        
        self.assertNotIn("contact_value", entry)
        self.assertNotIn("contact_method", entry)
        self.assertNotIn("registration_id", entry)  # Or if it is there, it's not leaking private contact.
        
        # Verify it has public safe fields
        self.assertEqual(entry["display_name"], "Player1")
        self.assertEqual(entry["total_points"], 10)

    def test_leaderboard_only_shows_approved_corrected_final(self) -> None:
        score = self.scoring_service.create_score(
            self.tournament.id,
            self.stage.id,
            self.group.id,
            self.round.id,
            ScoreCreateItem(registration_id=self.registration.id, placement=1),
        )
        
        # Draft score
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 0)

        # Submitted score
        score.status = ScoreStatus.SUBMITTED.value
        self.session.flush()
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 0)

        # Disputed score
        score.status = ScoreStatus.DISPUTED.value
        self.session.flush()
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 0)

        # Approved score
        score.status = ScoreStatus.APPROVED.value
        self.session.flush()
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 1)

        # Corrected score
        score.status = ScoreStatus.CORRECTED.value
        self.session.flush()
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 1)

        # Final score
        score.status = ScoreStatus.FINAL.value
        self.session.flush()
        results = self.leaderboard_service.public_leaderboard(self.tournament.id)
        self.assertEqual(len(results), 1)

if __name__ == "__main__":
    unittest.main()
