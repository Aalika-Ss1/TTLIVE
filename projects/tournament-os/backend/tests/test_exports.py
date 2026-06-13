import io
import sys
import unittest
import zipfile
from os import environ
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from tournament_os.api.main import app
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.database import Base, get_session
from tournament_os.models.competition import Group, Registration, Round, Stage
from tournament_os.models.identity import User
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.scoring import ScoreCreateItem


ADMIN_TOKEN = "test-admin-token"
ADMIN_HEADERS = {"x-admin-token": ADMIN_TOKEN}


class ExportTests(unittest.TestCase):
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
        
        app.dependency_overrides[get_session] = lambda: self.session
        self.client = TestClient(app)

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

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        app.dependency_overrides.clear()
        environ.pop("TOURNAMENT_OS_ADMIN_TOKEN", None)

    def test_export_leaderboard_xlsx_uses_admin_boundary_and_excludes_private_data(self) -> None:
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
        self.session.commit()

        missing_token_response = self.client.get(
            f"/admin/tournaments/{self.tournament.id}/exports/leaderboard.xlsx"
        )
        self.assertEqual(missing_token_response.status_code, 403)

        response = self.client.get(
            f"/admin/tournaments/{self.tournament.id}/exports/leaderboard.xlsx",
            headers=ADMIN_HEADERS,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(".xlsx", response.headers["content-disposition"])
        self.assertTrue(response.content.startswith(b"PK"))

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            self.assertIn("xl/worksheets/sheet1.xml", archive.namelist())
            sheet_xml = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")

        self.assertIn("rank", sheet_xml)
        self.assertIn("Player1", sheet_xml)
        self.assertIn("Lobby A", sheet_xml)
        self.assertIn(">10<", sheet_xml)
        self.assertIn(">1<", sheet_xml)
        self.assertNotIn("secret#1234", sheet_xml)
        self.assertNotIn("discord", sheet_xml)


if __name__ == "__main__":
    unittest.main()
