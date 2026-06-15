from datetime import timezone, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.enums import RegistrationStatus, TournamentStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import Registration
from tournament_os.models.identity import User
from tournament_os.models.tournament import Tournament
from tournament_os.schemas.registration import RegistrationCreate


class RegistrationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def submit_registration(self, tournament_id: str, payload: RegistrationCreate) -> Registration:
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        if tournament.status != TournamentStatus.REGISTRATION_OPEN.value:
            raise DomainError("registration_not_open", "Registration is not open.")

        existing = self.session.scalar(
            select(Registration).where(
                Registration.tournament_id == tournament_id,
                Registration.user_id == payload.user_id,
            )
        )
        if existing is not None:
            raise DomainError("registration_duplicate", "You already registered for this tournament.")

        duplicate_uid = self.session.scalar(
            select(Registration).where(
                Registration.tournament_id == tournament_id,
                Registration.game_uid == payload.game_uid,
            )
        )
        if duplicate_uid is not None:
            raise DomainError("game_uid_duplicate", "This game UID is already registered for this tournament.")

        registration = Registration(
            tournament_id=tournament_id,
            user_id=payload.user_id,
            status=RegistrationStatus.SUBMITTED.value,
            display_name=payload.display_name,
            in_game_name=payload.in_game_name,
            game_uid=payload.game_uid,
            contact_method=payload.contact_method,
            contact_value=payload.contact_value,
            submitted_at=datetime.now(timezone.utc),
        )
        self.session.add(registration)
        self.session.flush()
        self.audit_events.event(
            event_name="registration.submitted",
            entity_type="registration",
            entity_id=registration.id,
            tournament_id=tournament_id,
            payload={"user_id": payload.user_id},
        )
        self.session.flush()
        return registration

    def approve_registration(self, registration_id: str, actor_user_id: str | None = None) -> Registration:
        registration = self.session.get(Registration, registration_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found.")
        tournament = self.session.get(Tournament, registration.tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")

        if registration.status != RegistrationStatus.APPROVED.value:
            approved_count = self.session.scalar(
                select(func.count(Registration.id)).where(
                    Registration.tournament_id == registration.tournament_id,
                    Registration.status == RegistrationStatus.APPROVED.value,
                )
            ) or 0
            if approved_count >= tournament.max_participants:
                return self.waitlist_registration(registration_id, actor_user_id=actor_user_id)

        registration.status = RegistrationStatus.APPROVED.value
        registration.reviewed_by_user_id = actor_user_id
        registration.reviewed_at = datetime.now(timezone.utc)
        self.audit_events.audit(
            action="approve_registration",
            entity_type="registration",
            entity_id=registration_id,
            tournament_id=registration.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": registration.status},
        )
        self.audit_events.event(
            event_name="registration.approved",
            entity_type="registration",
            entity_id=registration_id,
            tournament_id=registration.tournament_id,
            payload={"user_id": registration.user_id},
        )
        
        # Phase 3: Discord Role Sync
        discord_identity = self.session.scalar(
            select(User.discord_id).where(User.id == registration.user_id)
        )
        if discord_identity:
            from tournament_os.application.discord import DiscordRoleService
            DiscordRoleService(self.session).assign_role_if_linked(
                tournament_id=registration.tournament_id,
                user_id=registration.user_id,
                discord_user_id=discord_identity,
                role_type="player"
            )
            
        self.session.flush()
        return registration

    def reject_registration(self, registration_id: str, reason: str, actor_user_id: str | None = None) -> Registration:
        registration = self.session.get(Registration, registration_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found.")
        registration.status = RegistrationStatus.REJECTED.value
        registration.reviewed_by_user_id = actor_user_id
        registration.reviewed_at = datetime.now(timezone.utc)
        self.audit_events.audit(
            action="reject_registration",
            entity_type="registration",
            entity_id=registration_id,
            tournament_id=registration.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": registration.status, "reason": reason},
        )
        self.audit_events.event(
            event_name="registration.rejected",
            entity_type="registration",
            entity_id=registration_id,
            tournament_id=registration.tournament_id,
            payload={"user_id": registration.user_id, "reason": reason},
        )
        self.session.flush()
        return registration

    def waitlist_registration(self, registration_id: str, actor_user_id: str | None = None) -> Registration:
        registration = self.session.get(Registration, registration_id)
        if registration is None:
            raise DomainError("registration_not_found", "Registration was not found.")
        registration.status = RegistrationStatus.WAITLISTED.value
        registration.reviewed_by_user_id = actor_user_id
        registration.reviewed_at = datetime.now(timezone.utc)
        self.audit_events.audit(
            action="waitlist_registration",
            entity_type="registration",
            entity_id=registration_id,
            tournament_id=registration.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": registration.status},
        )
        self.audit_events.event(
            event_name="registration.waitlisted",
            entity_type="registration",
            entity_id=registration_id,
            tournament_id=registration.tournament_id,
            payload={"user_id": registration.user_id},
        )
        self.session.flush()
        return registration
