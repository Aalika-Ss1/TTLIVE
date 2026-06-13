import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.application.registrations import RegistrationService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.application.tournaments import TournamentService
from tournament_os.database import Base
from tournament_os.models.competition import Registration, Score
from tournament_os.models.identity import User
from tournament_os.models.operations import AuditLog, EventOutbox
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.registration import RegistrationCreate
from tournament_os.schemas.scoring import ScoreCreateItem


class AuditEventTests(unittest.TestCase):
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
            name="Audit Test",
            game="Test",
            participant_type="solo",
            max_participants=8,
            registration_open_at=self.now,
            registration_close_at=self.now + timedelta(days=1),
            status="registration_open",
            public_slug="audit-test",
        )
        self.session.add(self.tournament)
        self.session.flush()

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_registration_approval_creates_audit_and_event(self) -> None:
        reg = RegistrationService(self.session).submit_registration(
            self.tournament.id,
            RegistrationCreate(
                user_id=self.player.id,
                display_name="P1",
                in_game_name="P1",
                game_uid="UID1",
                contact_method="discord",
                contact_value="123",
            ),
        )
        self.session.flush()

        # Approve registration
        RegistrationService(self.session).approve_registration(reg.id, actor_user_id=self.admin.id)
        
        # Verify AuditLog
        audit = self.session.scalar(
            select(AuditLog).where(AuditLog.entity_id == reg.id, AuditLog.action == "approve_registration")
        )
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor_user_id, self.admin.id)
        self.assertEqual(audit.after_json["status"], "approved")
        
        # Verify EventOutbox
        event = self.session.scalar(
            select(EventOutbox).where(EventOutbox.entity_id == reg.id, EventOutbox.event_name == "registration.approved")
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.payload_json["user_id"], self.player.id)
        
        # Ensure private fields are NOT in the payload
        self.assertNotIn("contact_value", event.payload_json)

    def test_score_approval_creates_audit_and_event(self) -> None:
        from tournament_os.models.competition import Group, GroupParticipant, Round, Stage
        
        formula = ScoreFormulaModel(
            id="f_1",
            tournament_id="t_1",
            name="MVP",
            placement_points_json={"1": 10},
            bonus_rules_json={},
            bye_rule_json={}
        )
        self.session.add(formula)
        self.tournament.active_score_formula_id = formula.id
        
        reg = Registration(id="reg_1", tournament_id=self.tournament.id, user_id=self.player.id, status="approved", display_name="P1", in_game_name="P1", game_uid="UID1", contact_method="discord", contact_value="123")
        stage = Stage(id="stg_1", tournament_id=self.tournament.id, name="Final", sequence=1, format="single_elimination")
        group = Group(id="grp_1", tournament_id=self.tournament.id, stage_id=stage.id, name="Group 1", sequence=1)
        round_ = Round(id="rnd_1", tournament_id=self.tournament.id, stage_id=stage.id, group_id=group.id, sequence=1, name="Round 1")
        part = GroupParticipant(id="gp_1", group_id=group.id, registration_id=reg.id, seed=1)
        
        self.session.add_all([reg, stage, group, round_, part])
        self.session.flush()

        score = ScoreEntryService(self.session).create_score(
            self.tournament.id,
            stage.id,
            group.id,
            round_.id,
            ScoreCreateItem(registration_id=reg.id, placement=1),
            submitted_by_user_id=self.admin.id
        )
        
        scoring_service = ScoreEntryService(self.session)
        scoring_service.submit_score(score.id, actor_user_id=self.admin.id)
        scoring_service.verify_score(score.id, actor_user_id=self.admin.id)
        scoring_service.approve_score(score.id, actor_user_id=self.admin.id)
        
        audit = self.session.scalar(
            select(AuditLog).where(AuditLog.entity_id == score.id, AuditLog.action == "approve_score")
        )
        self.assertIsNotNone(audit)
        self.assertEqual(audit.after_json["status"], "approved")
        
        event = self.session.scalar(
            select(EventOutbox).where(EventOutbox.entity_id == score.id, EventOutbox.event_name == "score.approved")
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.payload_json["total_points"], 10)

if __name__ == "__main__":
    unittest.main()
