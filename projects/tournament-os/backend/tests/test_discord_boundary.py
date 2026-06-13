import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tournament_os.application.discord import DiscordIntegrationService
from tournament_os.application.registrations import RegistrationService
from tournament_os.database import Base
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import Registration
from tournament_os.models.identity import User
from tournament_os.models.tournament import Tournament
from tournament_os.schemas.registration import RegistrationCreate


class DiscordBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        
        self.session = Session(self.engine)
        self.now = datetime.now(timezone.utc)
        
        self.admin = User(id="admin_1", display_name="Admin", email="admin@local", role="super_admin")
        self.session.add(self.admin)
        self.session.flush()

        self.tournament = Tournament(
            id="t_1",
            created_by_user_id=self.admin.id,
            name="Discord Test",
            game="Test",
            participant_type="solo",
            max_participants=8,
            registration_open_at=self.now,
            registration_close_at=self.now + timedelta(days=1),
            status="registration_open",
            public_slug="discord-test",
        )
        self.session.add(self.tournament)
        self.session.flush()

        self.service = DiscordIntegrationService(self.session)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_discord_registration_does_not_leak_private_fields_in_status(self) -> None:
        # Register player via discord
        reg = self.service.register_player(
            tournament_id=self.tournament.id,
            discord_user_id="12345",
            discord_name="TestUser",
            in_game_name="InGameTest",
            game_id="UID123"
        )
        self.session.flush()

        status = self.service.player_status(self.tournament.id, "12345")
        
        # Verify status contains expected fields
        self.assertEqual(status["status"], "submitted")
        self.assertEqual(status["display_name"], "InGameTest")
        self.assertIn("allowed_actions", status)
        
        # Verify it DOES NOT leak contact_value or contact_method
        self.assertNotIn("contact_value", status)
        self.assertNotIn("contact_method", status)
        self.assertNotIn("12345", status.values())  # Discord ID shouldn't be bare in the status unless specifically requested, but it's not a value

    def test_discord_score_submit_fails_when_not_assigned(self) -> None:
        # Register player via discord
        reg = self.service.register_player(
            tournament_id=self.tournament.id,
            discord_user_id="12345",
            discord_name="TestUser",
            in_game_name="InGameTest",
            game_id="UID123"
        )
        self.session.flush()

        with self.assertRaises(DomainError) as context:
            self.service.submit_score_from_discord(
                tournament_id=self.tournament.id,
                discord_user_id="12345",
                round_name="Round 1",
                placement=1,
                kills=5,
                evidence_uri="https://example.com/image.png"
            )
            
        self.assertEqual(context.exception.code, "round_not_found")

    def test_leaderboard_returns_no_mock_data(self) -> None:
        leaderboard = self.service.leaderboard(self.tournament.id)
        # Should just be an empty list, not mock data
        self.assertEqual(leaderboard["leaderboard"], [])

if __name__ == "__main__":
    unittest.main()
