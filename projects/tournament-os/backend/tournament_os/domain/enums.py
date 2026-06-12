from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    TOURNAMENT_ADMIN = "tournament_admin"
    SCORE_ADMIN = "score_admin"
    REFEREE = "referee"
    PLAYER = "player"
    VIEWER = "viewer"

class ParticipantType(str, Enum):
    SOLO = "solo"
    DUO = "duo"
    SQUAD = "squad"
    TEAM = "team"

class TournamentStatus(str, Enum):
    DRAFT = "draft"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    GROUPING = "grouping"
    READY = "ready"
    LIVE = "live"
    SCORING = "scoring"
    REVIEW = "review"
    FINALIZED = "finalized"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

class RegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"
    WITHDRAWN = "withdrawn"

class StageStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    LIVE = "live"
    SCORING = "scoring"
    REVIEW = "review"
    FINALIZED = "finalized"

class GroupParticipantStatus(str, Enum):
    ASSIGNED = "assigned"
    CHECK_IN = "checked_in"
    NO_SHOW = "no_show"
    WITHDRAWN = "withdrawn"
    ADVANCED = "advanced"
    ELIMINATED = "eliminated"

class RoundStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    SCORING = "scoring"
    REVIEW = "review"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"

class CheckInSessionStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    LOCKED = "locked"
    ARCHIVED = "archived"

class CheckInStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    CHECKED_IN = "checked_in"
    LATE_CHECKED_IN = "late_checked_in"
    NO_SHOW_PENDING = "no_show_pending"
    NO_SHOW = "no_show"
    EXCUSED = "excused"
    REPLACED = "replaced"

class ScoreStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    DISPUTED = "disputed"
    CORRECTED = "corrected"
    FINAL = "final"

class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class TournamentModel(str, Enum):
    FIXED_POINTS = "fixed_points"
    GROUP_POINTS_QUALIFIER = "group_points_qualifier"
    LOBBY_SHUFFLE = "lobby_shuffle"
    BRACKET_KNOCKOUT = "bracket_knockout"
    CHECKMATE_FINAL = "checkmate_final"

class ScoreResetPolicy(str, Enum):
    RESET_EACH_STAGE = "reset_each_stage"
    CARRY_FORWARD = "carry_forward"

class AdvancementType(str, Enum):
    TOP_N_PER_LOBBY = "top_n_per_lobby"
    TOP_N_OVERALL = "top_n_overall"
    THRESHOLD = "threshold"
    ADMIN_SELECTION = "admin_selection"

class LobbyAssignmentType(str, Enum):
    RANDOM = "random"
    MANUAL = "manual"
    SEEDED = "seeded"
    SNAKE_SHUFFLE = "snake_shuffle"
    SCORE_BASED_SHUFFLE = "score_based_shuffle"

class ByeBehavior(str, Enum):
    NONE = "none"
    ADVANCE_ONLY = "advance_only"
    FIXED_POINTS = "fixed_points"
    AVERAGE_POINTS = "average_points"

# Keep the following for backward compatibility if needed
class MatchStatus(str, Enum):
    PENDING = "pending"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    DISPUTED = "disputed"

class RulesetType(str, Enum):
    GROUP_POINTS_QUALIFIER = "group_points_qualifier"
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"

class PlacementPoint(int, Enum):
    P1 = 10
    P2 = 6
    P3 = 5
    P4 = 4
    P5 = 3