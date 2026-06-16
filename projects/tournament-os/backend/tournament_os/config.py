from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

# Try to load .env from the backend root
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

from os import getenv


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "TOURNAMENT_OS_DATABASE_URL",
        "sqlite:///./tournament_os_demo.db",
    )
    app_name: str = "Tournament OS"
    app_version: str = "0.1.0"


settings = Settings()

