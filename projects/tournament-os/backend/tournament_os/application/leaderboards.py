from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.domain.enums import ScoreStatus
from tournament_os.domain.leaderboard import ScoreRecord, build_leaderboard
from tournament_os.domain.serializers import stream_leaderboard_dict
from tournament_os.models.competition import Group, Registration, Round, Score


class LeaderboardQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def public_leaderboard(self, tournament_id: str) -> list[dict[str, object]]:
        rows = self.session.execute(
            select(Score, Registration, Group, Round)
            .join(Registration, Registration.id == Score.registration_id)
            .join(Group, Group.id == Score.group_id)
            .join(Round, Round.id == Score.round_id)
            .where(
                Score.tournament_id == tournament_id,
                Score.status.in_([ScoreStatus.APPROVED.value, ScoreStatus.FINAL.value]),
            )
        ).all()
        records = [
            ScoreRecord(
                registration_id=registration.id,
                display_name=registration.display_name,
                round_sequence=round_model.sequence,
                placement=score.placement,
                total_points=score.total_points,
                status=ScoreStatus(score.status),
                group_name=group.name,
            )
            for score, registration, group, round_model in rows
        ]
        return [stream_leaderboard_dict(entry) for entry in build_leaderboard(records)]
