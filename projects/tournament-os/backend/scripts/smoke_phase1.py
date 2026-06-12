import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from tournament_os.application.advancement import AdvancementService
from tournament_os.application.grouping import GroupGenerationService
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.registrations import RegistrationService
from tournament_os.application.rules import RuleSetService
from tournament_os.application.scoring import ScoreEntryService
from tournament_os.application.tournaments import TournamentService
from tournament_os.config import settings
from tournament_os.database import Base
from tournament_os.domain.enums import UserRole
from tournament_os import models  # noqa: F401
from tournament_os.models.competition import Group, GroupParticipant, Round, Stage
from tournament_os.models.identity import User
from tournament_os.schemas.registration import RegistrationCreate
from tournament_os.schemas.scoring import ScoreCreateItem
from tournament_os.schemas.tournament import RuleSetCreate, TournamentCreate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Phase 1 Tournament OS smoke flow.")
    parser.add_argument(
        "--create-schema",
        action="store_true",
        help="Create tables from SQLAlchemy metadata before running. Use only for local/dev smoke databases.",
    )
    args = parser.parse_args()

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    if args.create_schema:
        Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        admin_email = f"admin-{run_id}@example.local"
        admin = session.scalar(select(User).where(User.email == admin_email))
        if admin is None:
            admin = User(
                display_name="Tournament Admin",
                email=admin_email,
                role=UserRole.SUPER_ADMIN.value,
            )
            session.add(admin)
            session.flush()

        now = datetime.now(timezone.utc)
        tournament = TournamentService(session).create_tournament(
            TournamentCreate(
                name="Golden Spatula Smoke Test",
                game="Golden Spatula",
                participant_type="solo",
                max_participants=16,
                registration_open_at=now,
                registration_close_at=now + timedelta(days=1),
                public_slug=f"golden-smoke-{now.strftime('%Y%m%d%H%M%S')}",
            ),
            created_by_user_id=admin.id,
        )
        session.flush()
        RuleSetService(session).create_rule_set(
            tournament.id,
            RuleSetCreate(name="Golden Spatula Smoke Rules", max_participants=16),
        )
        TournamentService(session).open_registration(tournament.id, actor_user_id=admin.id)

        registrations = []
        for index in range(1, 17):
            user = User(
                display_name=f"Player {index:02d}",
                email=f"player{index:02d}-{run_id}@example.local",
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
            RegistrationService(session).approve_registration(registration.id, actor_user_id=admin.id)
            registrations.append(registration)

        TournamentService(session).close_registration(tournament.id, actor_user_id=admin.id)
        generated = GroupGenerationService(session).generate_groups(
            tournament.id,
            strategy="random",
            create_check_in_sessions=True,
            actor_user_id=admin.id,
        )
        first_stage = session.scalar(
            select(Stage).where(Stage.tournament_id == tournament.id, Stage.sequence == 1)
        )
        first_stage_groups = list(
            session.scalars(
                select(Group)
                .where(Group.tournament_id == tournament.id, Group.stage_id == first_stage.id)
                .order_by(Group.sequence)
            )
        )
        scoring_service = ScoreEntryService(session)
        approved_scores = 0
        for group in first_stage_groups:
            participants = list(
                session.scalars(
                    select(GroupParticipant)
                    .where(GroupParticipant.group_id == group.id)
                    .order_by(GroupParticipant.seed)
                )
            )
            rounds = list(
                session.scalars(select(Round).where(Round.group_id == group.id).order_by(Round.sequence))
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
                    scoring_service.approve_score(score.id, actor_user_id=admin.id)
                    approved_scores += 1
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
            session.scalars(select(Round).where(Round.group_id == final_group.id).order_by(Round.sequence))
        )
        final_scores = 0
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
                scoring_service.approve_score(score.id, actor_user_id=admin.id)
                final_scores += 1
        winner = AdvancementService(session).publish_stage_winner(
            tournament.id,
            final_stage.id,
            actor_user_id=admin.id,
        )
        output = {
            "tournament_id": tournament.id,
            "public_slug": tournament.public_slug,
            "registrations": len(registrations),
            "generated": generated.__dict__,
            "approved_scores": approved_scores,
            "leaderboard_size": len(leaderboard),
            "leaderboard_top_3": leaderboard[:3],
            "advancement": advancement.__dict__,
            "final_assignment": assignment.__dict__,
            "final_scores": final_scores,
            "winner": winner.__dict__,
        }
        session.commit()

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
