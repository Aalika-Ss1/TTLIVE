from dataclasses import dataclass
from statistics import mean

from tournament_os.domain.enums import ScoreStatus

COUNTING_SCORE_STATUSES = {ScoreStatus.APPROVED, ScoreStatus.FINAL}


@dataclass(frozen=True)
class ScoreRecord:
    registration_id: str
    display_name: str
    round_sequence: int
    placement: int
    total_points: int
    status: ScoreStatus
    group_name: str | None = None


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    registration_id: str
    display_name: str
    total_points: int
    games_played: int
    first_place_count: int
    average_placement: float
    latest_game_points: int
    latest_game_placement: int
    group_name: str | None = None


def build_leaderboard(scores: list[ScoreRecord]) -> list[LeaderboardEntry]:
    grouped: dict[str, list[ScoreRecord]] = {}

    for score in scores:
        if score.status not in COUNTING_SCORE_STATUSES:
            continue
        grouped.setdefault(score.registration_id, []).append(score)

    entries_without_rank = []
    for registration_id, player_scores in grouped.items():
        ordered_scores = sorted(player_scores, key=lambda item: item.round_sequence)
        latest_score = ordered_scores[-1]
        total_points = sum(item.total_points for item in ordered_scores)
        placements = [item.placement for item in ordered_scores]

        entries_without_rank.append(
            LeaderboardEntry(
                rank=0,
                registration_id=registration_id,
                display_name=latest_score.display_name,
                total_points=total_points,
                games_played=len(ordered_scores),
                first_place_count=sum(1 for placement in placements if placement == 1),
                average_placement=mean(placements),
                latest_game_points=latest_score.total_points,
                latest_game_placement=latest_score.placement,
                group_name=latest_score.group_name,
            )
        )

    sorted_entries = sorted(
        entries_without_rank,
        key=lambda entry: (
            -entry.total_points,
            -entry.first_place_count,
            entry.average_placement,
            -entry.latest_game_points,
            entry.latest_game_placement,
            entry.display_name.casefold(),
        ),
    )

    return [
        LeaderboardEntry(
            rank=index + 1,
            registration_id=entry.registration_id,
            display_name=entry.display_name,
            total_points=entry.total_points,
            games_played=entry.games_played,
            first_place_count=entry.first_place_count,
            average_placement=entry.average_placement,
            latest_game_points=entry.latest_game_points,
            latest_game_placement=entry.latest_game_placement,
            group_name=entry.group_name,
        )
        for index, entry in enumerate(sorted_entries)
    ]
