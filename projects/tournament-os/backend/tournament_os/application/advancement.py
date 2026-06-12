from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.enums import ScoreStatus, TournamentStatus
from tournament_os.domain.errors import DomainError
from tournament_os.domain.leaderboard import ScoreRecord, build_leaderboard
from tournament_os.models.competition import Group, GroupParticipant, Registration, Round, Score, Stage
from tournament_os.models.tournament import RuleSet, Tournament


@dataclass(frozen=True)
class AdvancementResult:
    stage_id: str
    advanced_count: int
    eliminated_count: int
    advanced_registration_ids: list[str]


@dataclass(frozen=True)
class NextStageAssignmentResult:
    source_stage_id: str
    target_stage_id: str
    assigned_count: int
    target_group_ids: list[str]


@dataclass(frozen=True)
class WinnerResult:
    stage_id: str
    registration_id: str
    display_name: str
    total_points: int


class AdvancementService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def publish_stage_advancement(
        self,
        tournament_id: str,
        stage_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> AdvancementResult:
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        if tournament.active_rule_set_id is None:
            raise DomainError("rule_set_missing", "Tournament must have an active rule set.")
        stage = self.session.get(Stage, stage_id)
        if stage is None or stage.tournament_id != tournament_id:
            raise DomainError("stage_not_found", "Stage was not found.")

        rule_set = self.session.get(RuleSet, tournament.active_rule_set_id)
        if rule_set is None:
            raise DomainError("rule_set_missing", "Rule set was not found.")
        top_n = int(rule_set.advancement_policy_json.get("top_n", 4))

        stage_groups = list(
            self.session.scalars(
                select(Group).where(Group.stage_id == stage_id).order_by(Group.sequence)
            )
        )
        if not stage_groups:
            raise DomainError("groups_not_found", "No groups were found for this stage.")

        advanced_ids: list[str] = []
        eliminated_count = 0

        for group in stage_groups:
            leaderboard = self._group_leaderboard(group.id)
            advancing_for_group = {entry.registration_id for entry in leaderboard[:top_n]}
            group_participants = list(
                self.session.scalars(
                    select(GroupParticipant).where(GroupParticipant.group_id == group.id)
                )
            )
            for participant in group_participants:
                if participant.registration_id in advancing_for_group:
                    participant.status = "advanced"
                    advanced_ids.append(participant.registration_id)
                else:
                    participant.status = "eliminated"
                    eliminated_count += 1

        self.audit_events.audit(
            action="publish_advancement",
            entity_type="stage",
            entity_id=stage_id,
            tournament_id=tournament_id,
            actor_user_id=actor_user_id,
            after={
                "advanced_count": len(advanced_ids),
                "eliminated_count": eliminated_count,
            },
        )
        self.audit_events.event(
            event_name="advancement.updated",
            entity_type="stage",
            entity_id=stage_id,
            tournament_id=tournament_id,
            payload={
                "advanced_count": len(advanced_ids),
                "eliminated_count": eliminated_count,
            },
        )
        self.session.flush()
        return AdvancementResult(
            stage_id=stage_id,
            advanced_count=len(advanced_ids),
            eliminated_count=eliminated_count,
            advanced_registration_ids=advanced_ids,
        )

    def assign_advanced_to_next_stage(
        self,
        tournament_id: str,
        source_stage_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> NextStageAssignmentResult:
        source_stage = self.session.get(Stage, source_stage_id)
        if source_stage is None or source_stage.tournament_id != tournament_id:
            raise DomainError("stage_not_found", "Source stage was not found.")

        target_stage = self.session.scalar(
            select(Stage)
            .where(
                Stage.tournament_id == tournament_id,
                Stage.sequence == source_stage.sequence + 1,
            )
            .limit(1)
        )
        if target_stage is None:
            raise DomainError("next_stage_not_found", "Next stage was not found.")

        target_groups = list(
            self.session.scalars(
                select(Group).where(Group.stage_id == target_stage.id).order_by(Group.sequence)
            )
        )
        if not target_groups:
            raise DomainError("groups_not_found", "No groups exist in the next stage.")

        source_group_ids = [
            group.id
            for group in self.session.scalars(
                select(Group).where(Group.stage_id == source_stage_id).order_by(Group.sequence)
            )
        ]
        advanced_participants = list(
            self.session.scalars(
                select(GroupParticipant)
                .where(
                    GroupParticipant.group_id.in_(source_group_ids),
                    GroupParticipant.status == "advanced",
                )
                .order_by(GroupParticipant.seed, GroupParticipant.registration_id)
            )
        )
        if not advanced_participants:
            raise DomainError("advanced_players_missing", "Publish advancement before assigning the next stage.")

        existing_target_assignments = self.session.scalar(
            select(GroupParticipant).where(GroupParticipant.group_id.in_([group.id for group in target_groups])).limit(1)
        )
        if existing_target_assignments is not None:
            raise DomainError("target_stage_already_assigned", "Next stage already has participant assignments.")

        assigned_count = 0
        for index, participant in enumerate(advanced_participants):
            target_group = target_groups[index % len(target_groups)]
            seed = (index // len(target_groups)) + 1
            self.session.add(
                GroupParticipant(
                    group_id=target_group.id,
                    registration_id=participant.registration_id,
                    seed=seed,
                    status="assigned",
                )
            )
            assigned_count += 1

        target_stage.status = "ready"
        self.audit_events.audit(
            action="assign_next_stage",
            entity_type="stage",
            entity_id=target_stage.id,
            tournament_id=tournament_id,
            actor_user_id=actor_user_id,
            after={"assigned_count": assigned_count},
        )
        self.audit_events.event(
            event_name="advancement.assigned_next_stage",
            entity_type="stage",
            entity_id=target_stage.id,
            tournament_id=tournament_id,
            payload={"assigned_count": assigned_count},
        )
        self.session.flush()
        return NextStageAssignmentResult(
            source_stage_id=source_stage_id,
            target_stage_id=target_stage.id,
            assigned_count=assigned_count,
            target_group_ids=[group.id for group in target_groups],
        )

    def publish_stage_winner(
        self,
        tournament_id: str,
        stage_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> WinnerResult:
        stage = self.session.get(Stage, stage_id)
        if stage is None or stage.tournament_id != tournament_id:
            raise DomainError("stage_not_found", "Stage was not found.")
        groups = list(
            self.session.scalars(
                select(Group).where(Group.stage_id == stage_id).order_by(Group.sequence)
            )
        )
        if not groups:
            raise DomainError("groups_not_found", "No groups were found for this stage.")

        all_entries = []
        for group in groups:
            all_entries.extend(self._group_leaderboard(group.id))
        if not all_entries:
            raise DomainError("scores_missing", "Approved scores are required before publishing winner.")
        winner = sorted(
            all_entries,
            key=lambda entry: (
                -entry.total_points,
                -entry.first_place_count,
                entry.average_placement,
                -entry.latest_game_points,
                entry.latest_game_placement,
                entry.display_name.casefold(),
            ),
        )[0]

        stage.status = "finalized"
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is not None:
            tournament.status = TournamentStatus.FINALIZED.value
        self.audit_events.audit(
            action="publish_winner",
            entity_type="stage",
            entity_id=stage_id,
            tournament_id=tournament_id,
            actor_user_id=actor_user_id,
            after={
                "registration_id": winner.registration_id,
                "display_name": winner.display_name,
                "total_points": winner.total_points,
            },
        )
        self.audit_events.event(
            event_name="winner.published",
            entity_type="stage",
            entity_id=stage_id,
            tournament_id=tournament_id,
            payload={
                "registration_id": winner.registration_id,
                "display_name": winner.display_name,
                "total_points": winner.total_points,
            },
        )
        self.session.flush()
        return WinnerResult(
            stage_id=stage_id,
            registration_id=winner.registration_id,
            display_name=winner.display_name,
            total_points=winner.total_points,
        )

    def _group_leaderboard(self, group_id: str):
        rows = self.session.execute(
            select(Score, Registration, Round)
            .join(Registration, Registration.id == Score.registration_id)
            .join(Round, Round.id == Score.round_id)
            .where(
                Score.group_id == group_id,
                Score.status.in_([ScoreStatus.APPROVED.value, ScoreStatus.FINAL.value]),
            )
        ).all()
        if not rows:
            raise DomainError("scores_missing", "Approved scores are required before publishing advancement.")
        return build_leaderboard(
            [
                ScoreRecord(
                    registration_id=registration.id,
                    display_name=registration.display_name,
                    round_sequence=round_model.sequence,
                    placement=score.placement,
                    total_points=score.total_points,
                    status=ScoreStatus(score.status),
                )
                for score, registration, round_model in rows
            ]
        )
