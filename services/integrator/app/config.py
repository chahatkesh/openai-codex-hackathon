from pathlib import Path

from pydantic_settings import BaseSettings


def _find_env_file() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return current.parents[2] / ".env"


_ENV_FILE = _find_env_file()


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4"
    openai_reasoning_effort: str = "medium"
    discovery_model: str = "gpt-5.4-mini"
    discovery_reasoning_effort: str = "low"
    reader_model: str = "gpt-5.4"
    reader_reasoning_effort: str = "medium"
    codegen_model: str = "gpt-5.4"
    codegen_reasoning_effort: str = "high"
    test_fix_model: str = "gpt-5.4"
    test_fix_reasoning_effort: str = "high"
    platform_api_url: str = "http://localhost:8000"
    max_fix_attempts: int = 3
    docs_fetch_timeout_seconds: int = 30
    docs_fetch_max_pages: int = 5
    docs_fetch_max_bytes: int = 2_000_000
    docs_fetch_user_agent: str = "FuseKit-Integrator/1.0"
    docs_fetch_render_js: bool = True
    docs_fetch_render_timeout_seconds: int = 20
    docs_fetch_parse_pdf: bool = True
    docs_fetch_parse_openapi: bool = True
    docs_fetch_extract_code_blocks: bool = True
    github_token: str = ""
    github_api_base_url: str = "https://api.github.com"
    github_default_owner: str = ""
    github_default_repo: str = ""
    github_default_base_branch: str = ""
    github_branch_prefix: str = "fusekit/publish"
    github_draft_prs: bool = True
    artifact_backend: str = "local"
    artifact_bucket: str = "fusekit-artifacts"
    artifact_s3_endpoint_url: str = "http://localhost:9000"
    artifact_s3_access_key: str = "minioadmin"
    artifact_s3_secret_key: str = "minioadmin"
    artifact_s3_region: str = "us-east-1"
    artifact_s3_force_path_style: bool = True

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
