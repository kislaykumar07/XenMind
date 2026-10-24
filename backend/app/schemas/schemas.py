from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ScenarioOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    user_message: str
    expected_outcome: str
    tags: list[str] = []
    assertions: list[dict[str, Any]] = []
    is_custom: bool = False
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class ScenarioDetail(ScenarioOut):
    context: dict[str, Any] = {}
    created_at: Optional[datetime] = None


class AgentVersionCreate(BaseModel):
    id: Optional[str] = Field(default=None, max_length=80)
    name: str = Field(..., min_length=1, max_length=200)
    version: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=2000)
    config: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False

    @field_validator("config")
    @classmethod
    def config_size(cls, v):
        if len(str(v)) > 8000:
            raise ValueError("config is too large")
        return v


class AgentVersionOut(BaseModel):
    id: str
    name: str
    version: str
    description: str
    config: dict[str, Any] = {}
    is_default: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RunCreate(BaseModel):
    scenario_id: str = Field(..., min_length=1, max_length=80)
    agent_version_id: Optional[str] = Field(default=None, max_length=80)
    workspace_id: Optional[str] = Field(default=None, max_length=80)


class ScenarioCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., min_length=1, max_length=80)
    user_message: str = Field(..., min_length=1, max_length=4000)
    expected_outcome: str = Field(..., min_length=1, max_length=80)
    tags: list[str] = []
    context: dict[str, Any] = {}
    assertions: list[dict[str, Any]] = []

    @field_validator("id")
    @classmethod
    def id_slug(cls, v):
        import re as _re

        if not _re.fullmatch(r"[a-z0-9][a-z0-9\-_]*", v):
            raise ValueError("id must be lowercase letters, digits, - or _")
        return v


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=10)


class AuthResponse(BaseModel):
    email: str
    name: str
    picture: str
    token: str


class LLMTestRequest(BaseModel):
    provider: str = Field(default="groq", max_length=20)
    model: Optional[str] = Field(default=None, max_length=120)


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class WorkspaceOut(BaseModel):
    id: str
    name: str
    join_code: str
    role: str = "member"
    member_count: int = 0

    model_config = {"from_attributes": True}


class WorkspaceJoin(BaseModel):
    code: str = Field(..., min_length=1, max_length=16)


class ScheduleCreate(BaseModel):
    name: str = Field(default="Nightly suite", max_length=200)
    agent_version_id: str = Field(..., max_length=80)
    workspace_id: Optional[str] = Field(default=None, max_length=80)
    webhook_url: Optional[str] = Field(default=None, max_length=500)


class ScheduleOut(BaseModel):
    id: str
    name: str
    agent_version_id: str
    workspace_id: Optional[str] = None
    webhook_url: Optional[str] = None
    enabled: bool
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_summary: dict[str, Any] = {}

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    schedule_id: Optional[str] = None
    kind: str
    message: str
    run_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BillingCheckoutRequest(BaseModel):
    plan: str = Field(..., max_length=20)


class BillingVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class AssertionResultOut(BaseModel):
    assertion_id: str
    description: str
    passed: bool
    expected: str
    actual: str
    explanation: str

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    id: str
    scenario_id: str
    agent_version_id: str
    status: str
    outcome: str
    final_response: str
    duration_ms: Optional[int] = None
    passed_count: int
    total_count: int
    replay_of_run_id: Optional[str] = None
    workspace_id: Optional[str] = None
    agent_kind: str = "mock"
    model: Optional[str] = None
    started_at: datetime
    finished_at: datetime

    model_config = {"from_attributes": True}


class RunDetail(RunOut):
    assertions: list[AssertionResultOut] = []


class RunEventOut(BaseModel):
    seq: int
    event_type: str
    name: str
    payload: dict[str, Any] = {}
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReplayRequest(BaseModel):
    agent_version_id: Optional[str] = Field(default=None, max_length=80)


class CompareRequest(BaseModel):
    # Mode A: explicit run lists, paired by scenario_id
    left_run_ids: Optional[list[str]] = Field(default=None, max_length=100)
    right_run_ids: Optional[list[str]] = Field(default=None, max_length=100)
    # Mode B: latest run per scenario for each agent version
    baseline_agent_version_id: Optional[str] = None
    candidate_agent_version_id: Optional[str] = None


class CompareItem(BaseModel):
    scenario_id: str
    left_status: Optional[str] = None
    right_status: Optional[str] = None
    change: str  # newly_passed | newly_failed | unchanged_passed | unchanged_failed | only_left | only_right


class CompareResponse(BaseModel):
    summary: dict[str, int]
    items: list[CompareItem]


class HealthOut(BaseModel):
    status: str
    service: str
    version: str
    database: str
