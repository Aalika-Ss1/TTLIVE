import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from tournament_os.application.advancement import AdvancementService
from tournament_os.application.dashboard import DashboardQueryService
from tournament_os.application.grouping import GroupGenerationService
from tournament_os.application.groups import GroupQueryService
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.registrations import RegistrationService
from tournament_os.application.rules import RuleSetService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.application.tournaments import TournamentService
from tournament_os.database import Base
from tournament_os.domain.enums import UserRole
from tournament_os.models import *  # noqa: F403
from tournament_os.models.competition import Group, GroupParticipant, Round, Stage
from tournament_os.models.identity import User
from tournament_os.schemas.registration import RegistrationCreate
from tournament_os.schemas.scoring import ScoreCreateItem
from tournament_os.schemas.tournament import RuleSetCreate, TournamentCreate


class Phase1FlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)

    def test_sixteen_player_registration_and_group_generation_flow(self) -> None:
        with Session(self.engine) as session:
            admin = User(
                display_name="Admin",
                email="admin@example.local",
                role=UserRole.SUPER_ADMIN.value,
            )
            session.add(admin)
            session.flush()

            now = datetime.now(timezone.utc)
            tournament = TournamentService(session).create_tournament(
                TournamentCreate(
                    name="Golden Spatula Test",
                    game="Golden Spatula",
                    participant_type="solo",
                    max_participants=16,
                    registration_open_at=now,
                    registration_close_at=now + timedelta(days=1),
                    public_slug="golden-test",
                ),
                created_by_user_id=admin.id,
            )
            RuleSetService(session).create_rule_set(
                tournament.id,
                RuleSetCreate(name="Golden Spatula Test Rules", max_participants=16),
            )
            TournamentService(session).open_registration(tournament.id, actor_user_id=admin.id)

            for index in range(1, 17):
                user = User(
                    display_name=f"Player {index:02d}",
                    email=f"player{index:02d}@example.local",
                    role=UserRole.PLAYER.value,
                )
                session.add(user)
                session.flush()
                registration = RegistrationService(session).submit_registration(
                    tournament.id,
                    RegistrationCreate(
                        user_id=user.id,
                        display_name=f"Player {index:02d}",
                        in_game_name=f"Player{index:02d}",
                        game_uid=f"UID{index:04d}",
                        contact_method="discord",
                        contact_value=f"player{index:02d}",
                    ),
                )
                RegistrationService(session).approve_registration(
                    registration.id,
                    actor_user_id=admin.id,
                )

            TournamentService(session).close_registration(tournament.id, actor_user_id=admin.id)
            generated = GroupGenerationService(session).generate_groups(
                tournament.id,
                strategy="random",
                create_check_in_sessions=True,
                actor_user_id=admin.id,
            )

            assigned_count = session.scalar(select(func.count(GroupParticipant.id)))

            first_stage = session.scalar(
                select(Stage)
                .where(Stage.tournament_id == tournament.id, Stage.sequence == 1)
                .limit(1)
            )
            first_stage_groups = list(
                session.scalars(
                    select(Group)
                    .where(Group.tournament_id == tournament.id, Group.stage_id == first_stage.id)
                    .order_by(Group.sequence)
                )
            )
            scoring_service = ScoreEntryService(session)
            for group in first_stage_groups:
                participants = list(
                    session.scalars(
                        select(GroupParticipant)
                        .where(GroupParticipant.group_id == group.id)
                        .order_by(GroupParticipant.seed)
                    )
                )
                rounds = list(
                    session.scalars(
                        select(Round).where(Round.group_id == group.id).order_by(Round.sequence)
                    )
                )
                for round_model in rounds:
                    for placement, group_participant in enumerate(participants, start=1):
                        score = scoring_service.create_score(
                            tournament.id,
                            stage_id=round_model.stage_id,
                            group_id=group.id,
                            round_id=round_model.id,
                            payload=ScoreCreateItem(
                                registration_id=group_participant.registration_id,
                                placement=placement,
                            ),
                            submitted_by_user_id=admin.id,
                        )
                        scoring_service.submit_score(score.id, actor_user_id=admin.id)
                        scoring_service.verify_score(score.id, actor_user_id=admin.id)
                        scoring_service.approve_score(score.id, actor_user_id=admin.id)

            dashboard = DashboardQueryService(session).admin_dashboard(tournament.id)
            groups = GroupQueryService(session).admin_groups(tournament.id)
            leaderboard = LeaderboardQueryService(session).public_leaderboard(tournament.id)
            advancement = AdvancementService(session).publish_stage_advancement(
                tournament.id,
                first_stage.id,
                actor_user_id=admin.id,
            )
            assignment = AdvancementService(session).assign_advanced_to_next_stage(
                tournament.id,
                first_stage.id,
                actor_user_id=admin.id,
            )
            final_stage = session.get(Stage, assignment.target_stage_id)
            final_group = session.scalar(
                select(Group).where(Group.stage_id == final_stage.id).order_by(Group.sequence).limit(1)
            )
            final_participants = list(
                session.scalars(
                    select(GroupParticipant)
                    .where(GroupParticipant.group_id == final_group.id)
                    .order_by(GroupParticipant.seed)
                )
            )
            final_rounds = list(
                session.scalars(
                    select(Round).where(Round.group_id == final_group.id).order_by(Round.sequence)
                )
            )
            for round_model in final_rounds:
                for placement, group_participant in enumerate(final_participants, start=1):
                    score = scoring_service.create_score(
                        tournament.id,
                        stage_id=round_model.stage_id,
                        group_id=final_group.id,
                        round_id=round_model.id,
                        payload=ScoreCreateItem(
                            registration_id=group_participant.registration_id,
                            placement=placement,
                        ),
                        submitted_by_user_id=admin.id,
                    )
                    scoring_service.submit_score(score.id, actor_user_id=admin.id)
                    scoring_service.verify_score(score.id, actor_user_id=admin.id)
                    scoring_service.approve_score(score.id, actor_user_id=admin.id)
            winner = AdvancementService(session).publish_stage_winner(
                tournament.id,
                final_stage.id,
                actor_user_id=admin.id,
            )
            advanced_count = session.scalar(
                select(func.count(GroupParticipant.id)).where(GroupParticipant.status == "advanced")
            )
            eliminated_count = session.scalar(
                select(func.count(GroupParticipant.id)).where(GroupParticipant.status == "eliminated")
            )

        self.assertEqual(generated.stages_created, 2)
        self.assertEqual(generated.groups_created, 3)
        self.assertEqual(generated.rounds_created, 7)
        self.assertEqual(generated.check_in_sessions_created, 2)
        self.assertEqual(assigned_count, 16)
        self.assertEqual(dashboard["registration_counts"]["approved"], 16)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]["groups"]), 2)
        self.assertEqual(len(leaderboard), 16)
        self.assertEqual(leaderboard[0]["total_points"], 20)
        self.assertNotIn("contact_value", leaderboard[0])
        self.assertEqual(advancement.advanced_count, 8)
        self.assertEqual(advancement.eliminated_count, 8)
        self.assertEqual(advanced_count, 8)
        self.assertEqual(eliminated_count, 8)
        self.assertEqual(assignment.assigned_count, 8)
        self.assertEqual(len(final_participants), 8)
        self.assertEqual(winner.total_points, 30)
        self.assertTrue(winner.display_name.startswith("Player "))


if __name__ == "__main__":
    unittest.main()
