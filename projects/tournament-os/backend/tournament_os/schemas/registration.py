from tournament_os.schemas.common import ApiModel


class RegistrationCreate(ApiModel):
    user_id: str
    display_name: str
    in_game_name: str
    game_uid: str
    contact_method: str
    contact_value: str


class RegistrationRead(ApiModel):
    id: str
    tournament_id: str
    user_id: str
    display_name: str
    in_game_name: str
    game_uid: str
    status: str


class AdminRegistrationRead(RegistrationRead):
    contact_method: str
    contact_value: str
    review_note: str | None = None
