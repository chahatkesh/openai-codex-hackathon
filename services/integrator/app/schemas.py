from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class IntegrateRequest(BaseModel):
    job_id: UUID
    docs_url: HttpUrl
    requested_by: Literal["user", "mcp_tool_miss", "crawler"] = "user"
    requested_tool_name: str | None = None


class IntegrateResponse(BaseModel):
    job_id: UUID
    status: str


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    current_stage: str | None = None
    attempts: int
    error_log: str | None = None
    resulting_tool_id: UUID | None = None
    requested_tool_name: str | None = None
    docs_url: str
    created_at: datetime
    completed_at: datetime | None = None


class DiscoveryResult(BaseModel):
    provider_name: str
    base_url: str | None = None
    auth_method: Literal["api_key", "bearer", "oauth", "none", "unknown"] = "unknown"
    key_endpoints: list[str] = Field(default_factory=list)
    rate_limits: str | None = None
    sandbox_available: bool = False


class APISpecification(BaseModel):
    provider_name: str
    base_url: str | None = None
    endpoints: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    auth: dict[str, Any] = Field(default_factory=dict)


class GeneratedTool(BaseModel):
    name: str
    description: str
    provider: str
    cost_per_call: int = 10
    status: Literal["live", "pending_credentials", "deprecated"] = "live"
    category: Literal[
        "communication", "data_retrieval", "search", "payments", "productivity", "other"
    ] = "other"
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] = Field(default_factory=dict)
    source: Literal["manual", "pipeline", "seed"] = "pipeline"
    version: int = 1
    implementation_module: str = "generated.execute"
    python_code: str


class TestResult(BaseModel):
    success: bool
    final_code: str
    attempts: int = 0
    error_log: str | None = None


class PipelineContext(BaseModel):
    job_id: UUID
    docs_url: str
    requested_by: str
    requested_tool_name: str | None = None
