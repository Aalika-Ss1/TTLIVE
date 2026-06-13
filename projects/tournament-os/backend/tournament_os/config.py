from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    database_url: str = getenv(
        "TOURNAMENT_OS_DATABASE_URL",
        "postgresql+psycopg://tournament_os:tournament_os@localhost:5433/tournament_os",
    )
    app_name: str = "Tournament OS"
    app_version: str = "0.1.0"


settings = Settings()

