import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tournament_os.application.checkins import CheckInService
from tournament_os.application.registrations import RegistrationService
from tournament_os.application.tournaments import TournamentService
from tournament_os.database import Base
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import CheckInSession
from tournament_os.models.identity import User
from tournament_os.models.tournament import Tournament
from tournament_os.schemas.registration import RegistrationCreate
from tournament_os.schemas.tournament import TournamentCreate


class CheckInTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        
        self.session = Session(self.engine)
        self.now = datetime.now(timezone.utc)
        
        # Setup basic tournament
        self.admin = User(id="admin_1", display_name="Admin", email="admin@local", role="super_admin")
        self.player = User(id="player_1", display_name="P1", email="p1@local", role="player")
        self.session.add_all([self.admin, self.player])
        self.session.flush()

        self.tournament = TournamentService(self.session).create_tournament(
            TournamentCreate(
                name="Test Check-in",
                game="Test",
                participant_type="solo",
                max_participants=16,
                registration_open_at=self.now,
                registration_close_at=self.now + timedelta(days=1),
                public_slug="test-check-in",
            ),
            created_by_user_id=self.admin.id,
        )
        TournamentService(self.session).open_registration(self.tournament.id, actor_user_id=self.admin.id)
        
        self.reg = RegistrationService(self.session).submit_registration(
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

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_ineligible_player_blocked(self) -> None:
        # Player is 'submitted', not 'approved'
        chk_session = CheckInSession(
            id="chk_1",
            tournament_id=self.tournament.id,
            stage_id="stage_1",
            name="R1 Checkin",
            session_type="stage",
            status="open",
            opens_at=self.now,
            closes_at=self.now + timedelta(hours=1),
        )
        self.session.add(chk_session)
        self.session.flush()

        with self.assertRaises(DomainError) as context:
            CheckInService(self.session).check_in(
                self.tournament.id,
                chk_session.id,
                self.reg.id,
                actor_user_id=self.player.id
            )
        self.assertEqual(context.exception.code, "registration_not_eligible")

    def test_check_in_before_open_time_rejected(self) -> None:
        # Approve player
        RegistrationService(self.session).approve_registration(self.reg.id, actor_user_id=self.admin.id)
        
        # Session opens in the future
        future_time = self.now + timedelta(hours=1)
        chk_session = CheckInSession(
            id="chk_2",
            tournament_id=self.tournament.id,
            stage_id="stage_1",
            name="R1 Checkin Future",
            session_type="stage",
            status="open",
            opens_at=future_time,
            closes_at=future_time + timedelta(hours=1),
        )
        self.session.add(chk_session)
        self.session.flush()

        with self.assertRaises(DomainError) as context:
            CheckInService(self.session).check_in(
                self.tournament.id,
                chk_session.id,
                self.reg.id,
                actor_user_id=self.player.id
            )
        # Expected to fail because check_ins.py doesn't check opens_at yet, so this test might fail (meaning the code needs fixing)
        # We write it according to the spec: "Check-in before open time is rejected."
        self.assertEqual(context.exception.code, "check_in_not_open")

    def test_check_in_after_close_time_rejected(self) -> None:
        RegistrationService(self.session).approve_registration(self.reg.id, actor_user_id=self.admin.id)
        
        past_time = self.now - timedelta(hours=2)
        chk_session = CheckInSession(
            id="chk_3",
            tournament_id=self.tournament.id,
            stage_id="stage_1",
            name="R1 Checkin Past",
            session_type="stage",
            status="open",
            opens_at=past_time,
            closes_at=past_time + timedelta(hours=1),
        )
        self.session.add(chk_session)
        self.session.flush()

        with self.assertRaises(DomainError) as context:
            CheckInService(self.session).check_in(
                self.tournament.id,
                chk_session.id,
                self.reg.id,
                actor_user_id=self.player.id
            )
        self.assertEqual(context.exception.code, "check_in_closed")

    def test_duplicate_check_in_idempotent(self) -> None:
        RegistrationService(self.session).approve_registration(self.reg.id, actor_user_id=self.admin.id)
        
        chk_session = CheckInSession(
            id="chk_4",
            tournament_id=self.tournament.id,
            stage_id="stage_1",
            name="R1 Checkin Valid",
            session_type="stage",
            status="open",
            opens_at=self.now - timedelta(hours=1),
            closes_at=self.now + timedelta(hours=1),
        )
        self.session.add(chk_session)
        self.session.flush()

        check_in_1 = CheckInService(self.session).check_in(
            self.tournament.id,
            chk_session.id,
            self.reg.id,
            actor_user_id=self.player.id
        )
        
        check_in_2 = CheckInService(self.session).check_in(
            self.tournament.id,
            chk_session.id,
            self.reg.id,
            actor_user_id=self.player.id
        )
        
        self.assertEqual(check_in_1.id, check_in_2.id)

if __name__ == "__main__":
    unittest.main()
