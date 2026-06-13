import sys
import unittest
from os import environ
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from tournament_os.api.main import app
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.application.tournaments import TournamentService
from tournament_os.database import Base, get_session
from tournament_os.domain.enums import ScoreStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import Group, GroupParticipant, Registration, Round, Stage
from tournament_os.models.identity import User
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.scoring import ScoreCreateItem


ADMIN_TOKEN = "test-admin-token"
ADMIN_HEADERS = {"x-admin-token": ADMIN_TOKEN}


class ScoreLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        environ["TOURNAMENT_OS_ADMIN_TOKEN"] = ADMIN_TOKEN
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
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
        app.dependency_overrides[get_session] = lambda: self.session
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        app.dependency_overrides.clear()
        environ.pop("TOURNAMENT_OS_ADMIN_TOKEN", None)

    def _create_score(self):
        return self.scoring.create_score(
            self.tournament.id,
            self.stage.id,
            self.group.id,
            self.round.id,
            ScoreCreateItem(registration_id=self.reg.id, placement=1),
            submitted_by_user_id=self.admin.id,
        )

    def _submit_verify_approve(self, score):
        self.scoring.submit_score(score.id, actor_user_id=self.player.id)
        self.scoring.verify_score(score.id, actor_user_id=self.admin.id)
        self.scoring.approve_score(score.id, actor_user_id=self.admin.id)

    def test_score_transitions_draft_to_submitted(self) -> None:
        score = self._create_score()
        self.assertEqual(score.status, ScoreStatus.DRAFT.value)
        
        self.scoring.submit_score(score.id, actor_user_id=self.player.id)
        self.assertEqual(score.status, ScoreStatus.SUBMITTED.value)
        
    def test_pending_score_not_in_public_leaderboard(self) -> None:
        score = self._create_score()
        self.scoring.submit_score(score.id, actor_user_id=self.player.id)
        self.scoring.verify_score(score.id, actor_user_id=self.admin.id)
        
        leaderboard = LeaderboardQueryService(self.session).public_leaderboard(self.tournament.id)
        self.assertEqual(len(leaderboard), 0, "Pending score should not appear on public leaderboard")

        self.scoring.approve_score(score.id, actor_user_id=self.admin.id)
        leaderboard2 = LeaderboardQueryService(self.session).public_leaderboard(self.tournament.id)
        self.assertEqual(len(leaderboard2), 1, "Approved score should appear on public leaderboard")

    def test_correction_audit(self) -> None:
        score = self._create_score()
        self._submit_verify_approve(score)
        
        # Correct score
        self.scoring.correct_score(
            score.id,
            payload=ScoreCreateItem(registration_id=self.reg.id, placement=2),
            actor_user_id=self.admin.id,
            reason="testing correction"
        )
        
        self.assertEqual(score.status, ScoreStatus.CORRECTED.value)
        self.assertEqual(score.placement, 2)
        self.assertEqual(score.total_points, 8)

    def test_score_transitions_reject_and_final(self) -> None:
        score = self._create_score()
        
        self.scoring.submit_score(score.id, actor_user_id=self.player.id)
        self.scoring.reject_score(score.id, actor_user_id=self.admin.id)
        self.assertEqual(score.status, ScoreStatus.REJECTED.value)
        
        self.scoring.submit_score(score.id, actor_user_id=self.player.id)
        self.scoring.verify_score(score.id, actor_user_id=self.admin.id)
        self.scoring.approve_score(score.id, actor_user_id=self.admin.id)
        self.scoring.mark_score_final(score.id, actor_user_id=self.admin.id)
        self.assertEqual(score.status, ScoreStatus.FINAL.value)

    def test_approve_requires_pending_verification(self) -> None:
        score = self._create_score()

        with self.assertRaises(DomainError) as context:
            self.scoring.approve_score(score.id, actor_user_id=self.admin.id)

        self.assertEqual(context.exception.code, "score_state_invalid")
        self.assertEqual(score.status, ScoreStatus.DRAFT.value)

    def test_reject_does_not_reopen_corrected_or_final_scores(self) -> None:
        score = self._create_score()
        self._submit_verify_approve(score)

        self.scoring.correct_score(
            score.id,
            payload=ScoreCreateItem(registration_id=self.reg.id, placement=2),
            actor_user_id=self.admin.id,
            reason="accepted dispute correction",
        )
        with self.assertRaises(DomainError) as corrected_context:
            self.scoring.reject_score(score.id, actor_user_id=self.admin.id)
        self.assertEqual(corrected_context.exception.code, "score_state_invalid")

        score.status = ScoreStatus.APPROVED.value
        self.scoring.mark_score_final(score.id, actor_user_id=self.admin.id)
        with self.assertRaises(DomainError) as final_context:
            self.scoring.reject_score(score.id, actor_user_id=self.admin.id)
        self.assertEqual(final_context.exception.code, "score_state_invalid")

    def test_correction_requires_reason(self) -> None:
        score = self._create_score()
        self._submit_verify_approve(score)

        with self.assertRaises(DomainError) as context:
            self.scoring.correct_score(
                score.id,
                payload=ScoreCreateItem(registration_id=self.reg.id, placement=2),
                actor_user_id=self.admin.id,
                reason=" ",
            )

        self.assertEqual(context.exception.code, "score_correction_reason_required")

    def test_admin_routes_follow_submit_verify_finalize_lifecycle(self) -> None:
        score = self._create_score()

        missing_token_response = self.client.post(f"/admin/scores/{score.id}/submit")
        self.assertEqual(missing_token_response.status_code, 403)
        self.assertEqual(score.status, ScoreStatus.DRAFT.value)

        submit_response = self.client.post(
            f"/admin/scores/{score.id}/submit",
            headers=ADMIN_HEADERS,
        )
        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.json()["status"], ScoreStatus.SUBMITTED.value)

        verify_response = self.client.post(
            f"/admin/scores/{score.id}/verify",
            headers=ADMIN_HEADERS,
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.json()["status"], ScoreStatus.PENDING_VERIFICATION.value)

        approve_response = self.client.post(
            f"/admin/scores/{score.id}/approve",
            headers=ADMIN_HEADERS,
        )
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.json()["status"], ScoreStatus.APPROVED.value)

        finalize_response = self.client.post(
            f"/admin/scores/{score.id}/finalize",
            headers=ADMIN_HEADERS,
        )
        self.assertEqual(finalize_response.status_code, 200)
        self.assertEqual(finalize_response.json()["status"], ScoreStatus.FINAL.value)

if __name__ == "__main__":
    unittest.main()
