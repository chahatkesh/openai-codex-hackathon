from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    platform_api_url: str = "http://localhost:8000"
    max_fix_attempts: int = 3
    docs_fetch_provider: str = "auto"
    docs_fetch_timeout_seconds: int = 30
    docs_fetch_max_pages: int = 3
    firecrawl_api_key: str = ""
    firecrawl_api_url: str = "https://api.firecrawl.dev"
    firecrawl_crawl_limit: int = 5
    jina_api_key: str = ""
    jina_reader_base_url: str = "https://r.jina.ai/"

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
