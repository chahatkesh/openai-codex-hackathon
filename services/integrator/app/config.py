from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    platform_api_url: str = "http://localhost:8000"
    max_fix_attempts: int = 3

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
