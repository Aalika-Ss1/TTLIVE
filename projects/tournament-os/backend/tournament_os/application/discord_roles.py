from sqlalchemy import select
from sqlalchemy.orm import Session

class DiscordRoleService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def assign_role_if_linked(
        self,
        tournament_id: str,
        user_id: str,
        discord_user_id: str,
        role_type: str,
    ):
        from tournament_os.models.competition import DiscordRoleLink, DiscordRoleAssignment
        
        # Check if the tournament has a link for this role type
        link = self.session.scalar(
            select(DiscordRoleLink).where(
                DiscordRoleLink.tournament_id == tournament_id,
                DiscordRoleLink.role_type == role_type,
            )
        )
        if not link:
            return None

        # Check if an assignment already exists
        assignment = self.session.scalar(
            select(DiscordRoleAssignment).where(
                DiscordRoleAssignment.tournament_id == tournament_id,
                DiscordRoleAssignment.user_id == user_id,
                DiscordRoleAssignment.role_type == role_type,
            )
        )
        if assignment:
            if assignment.desired_role_id != link.role_id:
                assignment.desired_role_id = link.role_id
                assignment.sync_status = "pending"
            return assignment

        # Create a new assignment
        import uuid
        from datetime import datetime, timezone
        
        assignment = DiscordRoleAssignment(
            id=str(uuid.uuid4()),
            tournament_id=tournament_id,
            user_id=user_id,
            discord_user_id=discord_user_id,
            role_type=role_type,
            desired_role_id=link.role_id,
            last_known_has_role=False,
            sync_status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(assignment)
        self.session.flush()
        return assignment
