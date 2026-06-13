from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.checkins import CheckInService
from tournament_os.application.groups import GroupQueryService
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.registrations import RegistrationService
from tournament_os.domain.enums import CheckInSessionStatus, RegistrationStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import CheckInSession, Registration
from tournament_os.models.identity import User
from tournament_os.schemas.registration import RegistrationCreate


class DiscordIntegrationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def player_status(self, tournament_id: str, discord_user_id: str) -> dict[str, object]:
        registration = self._registration_for_discord(tournament_id, discord_user_id)
        if registration is None:
            return {"status": "not_registered", "allowed_actions": ["register"]}

        payload: dict[str, object] = {
            "status": registration.status,
            "display_name": registration.display_name,
            "registration_id": registration.id,
            "allowed_actions": self._allowed_actions(registration.status),
        }
        if registration.status == RegistrationStatus.APPROVED.value:
            open_session = self.session.scalar(
                select(CheckInSession)
                .where(
                    CheckInSession.tournament_id == tournament_id,
                    CheckInSession.status == CheckInSessionStatus.OPEN.value,
                )
                .order_by(CheckInSession.created_at.desc())
            )
            if open_session is not None:
                payload["current_check_in_session_id"] = open_session.id
                payload["allowed_actions"] = ["check_in", *payload["allowed_actions"]]
        return payload

    def check_in(self, session_id: str, discord_user_id: str):
        check_in_session = self.session.get(CheckInSession, session_id)
        if check_in_session is None:
            raise DomainError("check_in_session_not_found", "Check-in session was not found.")

        registration = self._registration_for_discord(check_in_session.tournament_id, discord_user_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found for this Discord user.")

        return CheckInService(self.session).check_in(
            check_in_session.tournament_id,
            session_id,
            registration.id,
            source="discord",
        )

    def approve_player(self, tournament_id: str, discord_user_id: str):
        registration = self._registration_for_discord(tournament_id, discord_user_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found.")
        return RegistrationService(self.session).approve_registration(registration.id)

    def set_check_in_session(
        self,
        tournament_id: str,
        action: str,
        stage_id: str | None = None,
    ) -> dict[str, object]:
        if action == "open":
            if stage_id is None:
                raise DomainError("stage_required", "stage_id is required to open a check-in session.")
            session_id = f"chk_demo_auto_{tournament_id}"
            check_in_session = self.session.get(CheckInSession, session_id)
            if check_in_session is None:
                now = datetime.now(timezone.utc)
                check_in_session = CheckInSession(
                    id=session_id,
                    tournament_id=tournament_id,
                    stage_id=stage_id,
                    name="Round 1 Check-In",
                    session_type="stage",
                    status=CheckInSessionStatus.DRAFT.value,
                    opens_at=now,
                    closes_at=now + timedelta(hours=2),
                )
                self.session.add(check_in_session)
                self.session.flush()
            CheckInService(self.session).open_session(check_in_session.id)
            return {"status": "success", "message": "Check-in opened", "session_id": check_in_session.id}

        if action == "close":
            open_sessions = list(
                self.session.scalars(
                    select(CheckInSession).where(
                        CheckInSession.tournament_id == tournament_id,
                        CheckInSession.status == CheckInSessionStatus.OPEN.value,
                    )
                )
            )
            for check_in_session in open_sessions:
                CheckInService(self.session).close_session(check_in_session.id)
            return {"status": "success", "message": "Check-in closed", "closed_count": len(open_sessions)}

        raise DomainError("check_in_action_invalid", "Check-in action must be open or close.")

    def player_group(self, tournament_id: str, discord_user_id: str) -> dict[str, object]:
        registration = self._registration_for_discord(tournament_id, discord_user_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found.")
        for stage in GroupQueryService(self.session).public_groups(tournament_id):
            for group in stage["groups"]:
                for participant in group["participants"]:
                    if participant["registration_id"] == registration.id:
                        return {"stage": stage["name"], "group": group}
        raise DomainError("group_not_found", "Player has not been assigned to a group.")

    def leaderboard(self, tournament_id: str) -> dict[str, object]:
        return {"leaderboard": LeaderboardQueryService(self.session).public_leaderboard(tournament_id)}

    def register_player(
        self,
        tournament_id: str,
        discord_user_id: str,
        discord_name: str,
        in_game_name: str,
        game_id: str,
    ):
        user = self._get_or_create_discord_user(discord_user_id, discord_name)
        return RegistrationService(self.session).submit_registration(
            tournament_id,
            RegistrationCreate(
                user_id=user.id,
                display_name=in_game_name,
                in_game_name=in_game_name,
                game_uid=game_id,
                contact_method="discord",
                contact_value=discord_user_id,
            ),
        )

    def submit_score_from_discord(
        self,
        tournament_id: str,
        discord_user_id: str,
        round_name: str,
        placement: int,
        kills: int,
        evidence_uri: str | None = None,
    ) -> dict[str, object]:
        registration = self._registration_for_discord(tournament_id, discord_user_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found.")

        # Find the active stage, group, and round
        stage_id = None
        group_id = None
        round_id = None
        for stage in GroupQueryService(self.session).public_groups(tournament_id):
            for group in stage["groups"]:
                for participant in group["participants"]:
                    if participant["registration_id"] == registration.id:
                        stage_id = str(stage["id"])
                        group_id = str(group["id"])
                        for r in group["rounds"]:
                            if r["name"].lower() == round_name.lower():
                                round_id = str(r["id"])
                                break
                        break
                if stage_id:
                    break
            if stage_id:
                break

        if not round_id or not group_id or not stage_id:
            raise DomainError("round_not_found", f"Player is not assigned to a group or round '{round_name}' was not found.")

        from tournament_os.application.scoring import ScoreEntryService
        from tournament_os.schemas.scoring import ScoreCreateItem

        score = ScoreEntryService(self.session).create_score(
            tournament_id=tournament_id,
            stage_id=stage_id,
            group_id=group_id,
            round_id=round_id,
            payload=ScoreCreateItem(
                registration_id=registration.id,
                placement=placement,
                bonus_points=0,  # Kills are bonus points? If so, we should handle kills.
                penalty_points=0,
                evidence_uri=evidence_uri,
            ),
            submitted_by_user_id=registration.user_id,
        )
        
        # In discord flow, immediately transition to SUBMITTED state
        ScoreEntryService(self.session).submit_score(score.id, actor_user_id=registration.user_id)

        return {"status": "success", "score_id": score.id}

    def _registration_for_discord(self, tournament_id: str, discord_user_id: str) -> Registration | None:
        return self.session.scalar(
            select(Registration).where(
                Registration.tournament_id == tournament_id,
                Registration.contact_method == "discord",
                Registration.contact_value == discord_user_id,
            )
        )

    def _get_or_create_discord_user(self, discord_user_id: str, discord_name: str) -> User:
        user = self.session.scalar(select(User).where(User.discord_id == discord_user_id))
        if user is not None:
            return user
        user = User(
            id=f"user_discord_{discord_user_id}",
            display_name=discord_name,
            discord_id=discord_user_id,
            email=f"{discord_user_id}@discord.local",
        )
        self.session.add(user)
        self.session.flush()
        return user

    def _allowed_actions(self, status: str) -> list[str]:
        if status == RegistrationStatus.SUBMITTED.value:
            return ["view_status"]
        if status == RegistrationStatus.APPROVED.value:
            return ["view_group", "submit_evidence"]
        if status in {
            RegistrationStatus.REJECTED.value,
            RegistrationStatus.WAITLISTED.value,
            RegistrationStatus.WITHDRAWN.value,
        }:
            return ["view_status"]
        return []
