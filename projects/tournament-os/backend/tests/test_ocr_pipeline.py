import io
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from tournament_os.api.main import app
from tournament_os.database import Base, get_session
from tournament_os.models.competition import Score, Group, Registration, Round, Stage
from tournament_os.models.identity import User
from tournament_os.models.tournament import Tournament, RuleSet, ScoreFormulaModel
from tournament_os.models.evidence import Attachment, OcrSuggestion

ADMIN_TOKEN = "test-admin-token"
ADMIN_HEADERS = {"x-admin-token": ADMIN_TOKEN}


class OcrPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["TOURNAMENT_OS_ADMIN_TOKEN"] = ADMIN_TOKEN

        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        app.dependency_overrides[get_session] = lambda: self.session
        self.client = TestClient(app)

        # Create basic tournament structure
        self.admin = User(id="admin_1", display_name="Admin", role="super_admin")
        self.player = User(id="player_1", display_name="Player 1", role="player")
        self.session.add_all([self.admin, self.player])
        self.session.flush()

        self.tournament = Tournament(
            id="t_1",
            name="Golden Spatula Test",
            game="Golden Spatula",
            participant_type="solo",
            max_participants=8,
            status="live",
            public_slug="golden-spatula-test"
        )
        self.session.add(self.tournament)
        self.session.flush()

        self.ruleset = RuleSet(
            id="rs_1",
            tournament_id=self.tournament.id,
            name="Test Rules",
            model="group_points_qualifier",
        )
        self.session.add(self.ruleset)
        self.session.flush()

        self.formula = ScoreFormulaModel(
            id="f_1",
            tournament_id=self.tournament.id,
            rule_set_id=self.ruleset.id,
            name="Test Formula",
            placement_points_json={"1": 10, "2": 8, "3": 6, "4": 5},
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
            game_uid="UID_1",
            display_name="Player 1",
            in_game_name="Player1",
            contact_method="discord",
            contact_value="player1#0000",
            status="approved",
        )
        self.session.add(self.registration)
        self.session.flush()

        self.stage = Stage(id="stage_1", tournament_id=self.tournament.id, name="Stage 1", sequence=1, format="swiss", status="live")
        self.session.add(self.stage)
        self.session.flush()

        self.group = Group(id="group_1", tournament_id=self.tournament.id, stage_id=self.stage.id, name="Lobby A", sequence=1)
        self.session.add(self.group)
        self.session.flush()

        self.round = Round(id="round_1", tournament_id=self.tournament.id, stage_id=self.stage.id, group_id=self.group.id, name="Round 1", sequence=1, status="scoring")
        self.session.add(self.round)
        self.session.flush()

        self.score = Score(
            id="score_1",
            tournament_id=self.tournament.id,
            stage_id=self.stage.id,
            group_id=self.group.id,
            round_id=self.round.id,
            registration_id=self.registration.id,
            placement=4,
            placement_points=5,
            bonus_points=0,
            penalty_points=0,
            bye_points=0,
            total_points=5,
            status="submitted",
            formula_snapshot_json={"placement_points": {"4": 5}},
        )
        self.session.add(self.score)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        app.dependency_overrides.clear()
        os.environ.pop("TOURNAMENT_OS_ADMIN_TOKEN", None)

    def test_upload_evidence_creates_attachment_and_ocr_suggestions(self) -> None:
        file_content = b"fake-png-image-contents-for-mock_test_1"
        file_data = {"file": ("mock_test_1.png", io.BytesIO(file_content), "image/png")}

        response = self.client.post(
            f"/admin/scores/{self.score.id}/evidence",
            files=file_data,
            headers=ADMIN_HEADERS
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)  # mock_test_1 returns 3 mock suggestions
        self.assertEqual(data[0]["player_name_raw"], "Player 07")
        self.assertEqual(data[0]["detected_placement"], 1)

        # Check DB records
        attachments = self.session.scalars(select(Attachment)).all()
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].filename, "mock_test_1.png")

        suggestions = self.session.scalars(select(OcrSuggestion)).all()
        self.assertEqual(len(suggestions), 3)

    def test_duplicate_evidence_upload_returns_bad_request(self) -> None:
        file_content = b"fake-png-image-contents-for-duplicate-test"
        file_data = {"file": ("mock_test_1.png", io.BytesIO(file_content), "image/png")}

        # First upload
        response1 = self.client.post(
            f"/admin/scores/{self.score.id}/evidence",
            files=file_data,
            headers=ADMIN_HEADERS
        )
        self.assertEqual(response1.status_code, 200)

        # Second upload with same content (same checksum)
        file_data_dup = {"file": ("mock_test_1.png", io.BytesIO(file_content), "image/png")}
        response2 = self.client.post(
            f"/admin/scores/{self.score.id}/evidence",
            files=file_data_dup,
            headers=ADMIN_HEADERS
        )
        self.assertEqual(response2.status_code, 400)
        self.assertIn("Duplicate evidence file", response2.json()["detail"])

    def test_get_pending_suggestions(self) -> None:
        # Create a mock attachment and suggestion
        attachment = Attachment(
            id="att_1",
            filename="test.png",
            file_path="/path/test.png",
            checksum="hash123",
            file_size=100
        )
        suggestion = OcrSuggestion(
            id="sug_1",
            attachment_id="att_1",
            score_id=self.score.id,
            player_name_raw="Player 07",
            detected_placement=1,
            confidence_score=0.95,
            status="pending"
        )
        self.session.add_all([attachment, suggestion])
        self.session.commit()

        response = self.client.get("/admin/ocr/suggestions", headers=ADMIN_HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "sug_1")

    def test_accept_suggestion_updates_score_and_transitions_status(self) -> None:
        # Create a mock attachment and suggestion
        attachment = Attachment(
            id="att_1",
            filename="test.png",
            file_path="/path/test.png",
            checksum="hash123",
            file_size=100
        )
        suggestion = OcrSuggestion(
            id="sug_1",
            attachment_id="att_1",
            score_id=self.score.id,
            player_name_raw="Player 1",
            detected_placement=2,
            confidence_score=0.95,
            status="pending"
        )
        self.session.add_all([attachment, suggestion])
        self.session.commit()

        response = self.client.post(f"/admin/ocr/suggestions/{suggestion.id}/accept", headers=ADMIN_HEADERS)
        if response.status_code != 200:
            print("ACCEPT FAILED:", response.status_code, response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "accepted")

        # Verify score placement was corrected to 2 (from original 4)
        self.session.expire(self.score)
        score_db = self.session.get(Score, self.score.id)
        self.assertEqual(score_db.placement, 2)
        self.assertEqual(score_db.status, "corrected")

    def test_reject_suggestion_updates_status_without_modifying_score(self) -> None:
        attachment = Attachment(
            id="att_1",
            filename="test.png",
            file_path="/path/test.png",
            checksum="hash123",
            file_size=100
        )
        suggestion = OcrSuggestion(
            id="sug_1",
            attachment_id="att_1",
            score_id=self.score.id,
            player_name_raw="Player 1",
            detected_placement=2,
            confidence_score=0.95,
            status="pending"
        )
        self.session.add_all([attachment, suggestion])
        self.session.commit()

        response = self.client.post(f"/admin/ocr/suggestions/{suggestion.id}/reject", headers=ADMIN_HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "rejected")

        # Verify score remains unchanged
        self.session.expire(self.score)
        score_db = self.session.get(Score, self.score.id)
        self.assertEqual(score_db.placement, 4)  # still original placement 4
