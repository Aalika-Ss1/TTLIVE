from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tournament_os.database import Base
from tournament_os.domain.enums import UserRole
from tournament_os.models.base import IdMixin, TimestampMixin


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    discord_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(40), default=UserRole.PLAYER.value)

    identities: Mapped[list["UserIdentity"]] = relationship(back_populates="user")

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_discord_id", "discord_id"),
    )


class UserIdentity(IdMixin, Base):
    __tablename__ = "user_identities"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))

    user: Mapped[User] = relationship(back_populates="identities")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_user_identities_provider_user"),
    )


class TournamentUserRole(IdMixin, Base):
    __tablename__ = "tournament_user_roles"

    tournament_id: Mapped[str] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", "role", name="uq_tournament_user_roles_scope"),
        Index("ix_tournament_user_roles_user", "tournament_id", "user_id"),
        Index("ix_tournament_user_roles_role", "tournament_id", "role"),
    )
