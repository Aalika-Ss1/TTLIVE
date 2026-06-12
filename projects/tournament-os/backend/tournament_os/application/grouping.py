from dataclasses import dataclass
from datetime import timedelta
from random import Random

from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.enums import RegistrationStatus, TournamentStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.base import utcnow
from tournament_os.models.competition import (
    CheckInSession,
    Group,
    GroupParticipant,
    Registration,
    Round,
    Stage,
)
from tournament_os.models.tournament import RuleSet, Tournament


@dataclass(frozen=True)
class GeneratedStructure:
    stages_created: int
    groups_created: int
    rounds_created: int
    participants_assigned: int
    check_in_sessions_created: int


def stage_group_counts(participant_count: int, lobby_size: int) -> list[tuple[str, int, int]]:
    if participant_count <= lobby_size:
        return [("Final", 1, 3)]
    if participant_count <= 16:
        return [("Round 1", 2, 2), ("Final", 1, 3)]
    if participant_count <= 32:
        return [("Round 1", 4, 2), ("Semi Final", 2, 2), ("Final", 1, 3)]
    if participant_count <= 64:
        return [("Round 1", 8, 2), ("Round 2", 4, 2), ("Semi Final", 2, 2), ("Final", 1, 3)]
    raise DomainError("participant_count_unsupported", "MVP supports up to 64 players.")


class GroupGenerationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def generate_groups(
        self,
        tournament_id: str,
        *,
        strategy: str = "random",
        create_check_in_sessions: bool = True,
        actor_user_id: str | None = None,
    ) -> GeneratedStructure:
        if strategy not in {"random", "manual"}:
            raise DomainError("group_strategy_invalid", "Phase 1 supports random or manual grouping.")

        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        if tournament.status not in {
            TournamentStatus.REGISTRATION_CLOSED.value,
            TournamentStatus.GROUPING.value,
        }:
            raise DomainError("tournament_state_invalid", "Groups can be generated after registration closes.")
        if tournament.active_rule_set_id is None:
            raise DomainError("rule_set_missing", "Tournament must have an active rule set.")

        existing_stage = self.session.scalar(select(Stage).where(Stage.tournament_id == tournament_id))
        if existing_stage is not None:
            raise DomainError("groups_already_generated", "Groups already exist for this tournament.")

        rule_set = self.session.get(RuleSet, tournament.active_rule_set_id)
        if rule_set is None:
            raise DomainError("rule_set_missing", "Active rule set was not found.")

        approved = list(
            self.session.scalars(
                select(Registration)
                .where(
                    Registration.tournament_id == tournament_id,
                    Registration.status == RegistrationStatus.APPROVED.value,
                )
                .order_by(Registration.created_at, Registration.id)
            )
        )
        if not approved:
            raise DomainError("no_approved_registrations", "No approved registrations are available for grouping.")

        participants = approved[:]
        if strategy == "random":
            Random(tournament_id).shuffle(participants)

        stages_created = 0
        groups_created = 0
        rounds_created = 0
        check_in_sessions_created = 0
        now = utcnow()

        for stage_index, (stage_name, group_count, games_per_group) in enumerate(
            stage_group_counts(len(participants), rule_set.lobby_size),
            start=1,
        ):
            stage = Stage(
                tournament_id=tournament_id,
                name=stage_name,
                sequence=stage_index,
                format=rule_set.model,
                status="ready" if stage_index == 1 else "draft",
            )
            self.session.add(stage)
            self.session.flush()
            stages_created += 1

            if create_check_in_sessions:
                session = CheckInSession(
                    tournament_id=tournament_id,
                    stage_id=stage.id,
                    name=f"{stage_name} Check-In",
                    session_type="stage",
                    status="draft",
                    opens_at=now + timedelta(days=stage_index - 1),
                    closes_at=now + timedelta(days=stage_index - 1, minutes=25),
                    created_by_user_id=actor_user_id,
                )
                self.session.add(session)
                check_in_sessions_created += 1

            for group_index in range(1, group_count + 1):
                group_name = f"{stage_name} Lobby {chr(64 + group_index)}"
                group = Group(
                    tournament_id=tournament_id,
                    stage_id=stage.id,
                    name=group_name,
                    sequence=group_index,
                )
                self.session.add(group)
                self.session.flush()
                groups_created += 1

                for round_index in range(1, games_per_group + 1):
                    self.session.add(
                        Round(
                            tournament_id=tournament_id,
                            stage_id=stage.id,
                            group_id=group.id,
                            name=f"{group_name} Game {round_index}",
                            sequence=round_index,
                            status="scheduled",
                        )
                    )
                    rounds_created += 1

                if stage_index == 1:
                    start = (group_index - 1) * rule_set.lobby_size
                    end = start + rule_set.lobby_size
                    for seed, registration in enumerate(participants[start:end], start=1):
                        self.session.add(
                            GroupParticipant(
                                group_id=group.id,
                                registration_id=registration.id,
                                seed=seed,
                                status="assigned",
                            )
                        )

        tournament.status = TournamentStatus.GROUPING.value
        self.audit_events.audit(
            action="generate_groups",
            entity_type="tournament",
            entity_id=tournament_id,
            tournament_id=tournament_id,
            actor_user_id=actor_user_id,
            after={"participants": len(participants), "stages": stages_created},
        )
        self.audit_events.event(
            event_name="groups.generated",
            entity_type="tournament",
            entity_id=tournament_id,
            tournament_id=tournament_id,
            payload={"participants": len(participants), "stages": stages_created},
        )
        self.session.flush()

        return GeneratedStructure(
            stages_created=stages_created,
            groups_created=groups_created,
            rounds_created=rounds_created,
            participants_assigned=len(participants),
            check_in_sessions_created=check_in_sessions_created,
        )
