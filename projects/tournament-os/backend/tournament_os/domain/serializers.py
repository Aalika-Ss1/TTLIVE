from dataclasses import dataclass

from tournament_os.domain.enums import RegistrationStatus
from tournament_os.domain.leaderboard import LeaderboardEntry


@dataclass(frozen=True)
class RegistrationRecord:
    id: str
    display_name: str
    in_game_name: str
    game_uid: str
    status: RegistrationStatus
    contact_method: str | None = None
    contact_value: str | None = None
    review_note: str | None = None


def public_registration_dict(registration: RegistrationRecord) -> dict[str, str]:
    return {
        "id": registration.id,
        "display_name": registration.display_name,
        "in_game_name": registration.in_game_name,
        "game_uid": registration.game_uid,
        "status": registration.status.value,
    }


def stream_leaderboard_dict(entry: LeaderboardEntry) -> dict[str, object]:
    return {
        "rank": entry.rank,
        "display_name": entry.display_name,
        "group_name": entry.group_name,
        "total_points": entry.total_points,
        "games_played": entry.games_played,
    }
