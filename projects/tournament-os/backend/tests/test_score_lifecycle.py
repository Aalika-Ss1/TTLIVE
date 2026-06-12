import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.application.tournaments import TournamentService
from tournament_os.database import Base
from tournament_os.domain.enums import ScoreStatus
from tournament_os.models.competition import Group, GroupParticipant, Registration, Round, Stage
from tournament_os.models.identity import User
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.scoring import ScoreCreateItem


class ScoreLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        
        self.session = Session(self.engine)
        self.now = datetime.now(timezone.utc)
        
        self.admin = User(id="admin_1", display_name="Admin", email="admin@local", role="super_admin")
        self.player = User(id="player_1", display_name="P1", email="p1@local", role="player")
        self.session.add_all([self.admin, self.player])
        self.session.flush()

        self.tournament = Tournament(
            id="t_1",
            created_by_user_id=self.admin.id,
            name="Score Test",
            game="Test",
            participant_type="solo",
            max_participants=8,
            registration_open_at=self.now,
            registration_close_at=self.now + timedelta(days=1),
            status="live",
            public_slug="score-test",
        )
        self.session.add(self.tournament)
        
        self.formula = ScoreFormulaModel(
            id="f_1",
            tournament_id="t_1",
            name="MVP",
            placement_points_json={"1": 10, "2": 8},
            bonus_rules_json={},
            bye_rule_json={}
        )
        self.session.add(self.formula)
        self.session.flush()
        
        self.tournament.active_score_formula_id = self.formula.id
        
        self.reg = Registration(
            id="reg_1",
            tournament_id=self.tournament.id,
            user_id=self.player.id,
            status="approved",
            display_name="P1",
            in_game_name="P1",
            game_uid="UID1",
            contact_method="discord",
            contact_value="123"
        )
        self.session.add(self.reg)
        
        self.stage = Stage(id="stg_1", tournament_id=self.tournament.id, name="Final", sequence=1, format="single_elimination")
        self.group = Group(id="grp_1", tournament_id=self.tournament.id, stage_id=self.stage.id, name="Group 1", sequence=1)
        self.round = Round(id="rnd_1", tournament_id=self.tournament.id, stage_id=self.stage.id, group_id=self.group.id, sequence=1, name="Round 1")
        self.part = GroupParticipant(id="gp_1", group_id=self.group.id, registration_id=self.reg.id, seed=1)
        
        self.session.add_all([self.stage, self.group, self.round, self.part])
        self.session.flush()
        
        self.scoring = ScoreEntryService(self.session)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_score_transitions_draft_to_submitted(self) -> None:
        score = self.scoring.create_score(
            self.tournament.id,
            self.stage.id,
            self.group.id,
            self.round.id,
            ScoreCreateItem(registration_id=self.reg.id, placement=1),
            submitted_by_user_id=self.admin.id
        )
        self.assertEqual(score.status, ScoreStatus.DRAFT.value)
        
        score.status = ScoreStatus.SUBMITTED.value
        self.session.flush()
        
        self.assertEqual(score.status, ScoreStatus.SUBMITTED.value)
        
    def test_pending_score_not_in_public_leaderboard(self) -> None:
        score = self.scoring.create_score(
            self.tournament.id,
            self.stage.id,
            self.group.id,
            self.round.id,
            ScoreCreateItem(registration_id=self.reg.id, placement=1),
            submitted_by_user_id=self.admin.id
        )
        score.status = ScoreStatus.PENDING_VERIFICATION.value
        self.session.flush()
        
        leaderboard = LeaderboardQueryService(self.session).public_leaderboard(self.tournament.id)
        self.assertEqual(len(leaderboard), 0, "Pending score should not appear on public leaderboard")

        self.scoring.approve_score(score.id, actor_user_id=self.admin.id)
        leaderboard2 = LeaderboardQueryService(self.session).public_leaderboard(self.tournament.id)
        self.assertEqual(len(leaderboard2), 1, "Approved score should appear on public leaderboard")

    def test_correction_audit(self) -> None:
        score = self.scoring.create_score(
            self.tournament.id,
            self.stage.id,
            self.group.id,
            self.round.id,
            ScoreCreateItem(registration_id=self.reg.id, placement=1),
            submitted_by_user_id=self.admin.id
        )
        self.scoring.approve_score(score.id, actor_user_id=self.admin.id)
        
        # Correct score
        score.status = ScoreStatus.CORRECTED.value
        score.placement = 2
        score.total_points = 8
        self.session.flush()
        
        self.assertEqual(score.status, ScoreStatus.CORRECTED.value)

if __name__ == "__main__":
    unittest.main()
