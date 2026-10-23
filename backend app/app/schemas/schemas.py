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
