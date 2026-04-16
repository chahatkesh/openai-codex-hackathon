from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit"
    database_url_sync: str = "postgresql://fusekit:fusekit@localhost:5432/fusekit"

    # API keys for tool providers (set via .env)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    nylas_api_key: str = ""
    nylas_grant_id: str = ""

    apify_api_token: str = ""

    producthunt_api_token: str = ""

    serper_api_key: str = ""  # for search_web

    resend_api_key: str = ""  # for send_email via Resend

    # Wallet defaults
    default_wallet_balance: int = 10000  # 10000 credits = $10 for demo

    # MCP server
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    public_base_url: str = "http://localhost:8000"
    integrator_url: str = "http://localhost:8001"
    demo_auth_token: str = "demo-token-fusekit-2026"

    # Artifact storage
    artifact_backend: str = "local"
    artifact_bucket: str = "fusekit-artifacts"
    artifact_s3_endpoint_url: str = "http://localhost:9000"
    artifact_s3_access_key: str = "minioadmin"
    artifact_s3_secret_key: str = "minioadmin"
    artifact_s3_region: str = "us-east-1"
    artifact_s3_force_path_style: bool = True

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
