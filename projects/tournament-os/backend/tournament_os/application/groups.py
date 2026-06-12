from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.models.competition import Group, GroupParticipant, Registration, Round, Stage


class GroupQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def admin_groups(self, tournament_id: str) -> list[dict[str, object]]:
        stages = list(
            self.session.scalars(
                select(Stage)
                .where(Stage.tournament_id == tournament_id)
                .order_by(Stage.sequence)
            )
        )
        output: list[dict[str, object]] = []
        for stage in stages:
            groups = list(
                self.session.scalars(
                    select(Group).where(Group.stage_id == stage.id).order_by(Group.sequence)
                )
            )
            output.append(
                {
                    "id": stage.id,
                    "name": stage.name,
                    "sequence": stage.sequence,
                    "status": stage.status,
                    "groups": [self._group_payload(group, include_private=False) for group in groups],
                }
            )
        return output

    def public_groups(self, tournament_id: str) -> list[dict[str, object]]:
        return self.admin_groups(tournament_id)

    def _group_payload(self, group: Group, include_private: bool) -> dict[str, object]:
        participants = self.session.execute(
            select(GroupParticipant, Registration)
            .join(Registration, Registration.id == GroupParticipant.registration_id)
            .where(GroupParticipant.group_id == group.id)
            .order_by(GroupParticipant.seed, Registration.display_name)
        ).all()
        rounds = list(
            self.session.scalars(
                select(Round).where(Round.group_id == group.id).order_by(Round.sequence)
            )
        )
        return {
            "id": group.id,
            "name": group.name,
            "sequence": group.sequence,
            "participants": [
                {
                    "registration_id": registration.id,
                    "display_name": registration.display_name,
                    "in_game_name": registration.in_game_name,
                    "seed": group_participant.seed,
                    "status": group_participant.status,
                }
                for group_participant, registration in participants
            ],
            "rounds": [
                {
                    "id": round_model.id,
                    "name": round_model.name,
                    "sequence": round_model.sequence,
                    "status": round_model.status,
                }
                for round_model in rounds
            ],
        }
