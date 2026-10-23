from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(80), primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False, default="")
    category = Column(String(80), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    expected_outcome = Column(String(80), nullable=False)
    tags = Column(JSON, nullable=False, default=list)
    context = Column(JSON, nullable=False, default=dict)
    assertions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id = Column(String(80), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=False, default="")
    config = Column(JSON, nullable=False, default=dict)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(80), ForeignKey("scenarios.id"), nullable=False, index=True)
    agent_version_id = Column(String(80), ForeignKey("agent_versions.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # passed | failed | error
    outcome = Column(String(80), nullable=False, default="")
    final_response = Column(Text, nullable=False, default="")
    duration_ms = Column(Integer, nullable=True)  # measured only, never invented
    passed_count = Column(Integer, nullable=False, default=0)
    total_count = Column(Integer, nullable=False, default=0)
    replay_of_run_id = Column(String(64), ForeignKey("test_runs.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    scenario = relationship("Scenario")
    agent_version = relationship("AgentVersion")
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan", order_by="RunEvent.seq")
    assertion_results = relationship(
        "AssertionResult", back_populates="run", cascade="all, delete-orphan", order_by="AssertionResult.id"
    )


class RunEvent(Base):
    __tablename__ = "run_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("test_runs.id"), nullable=False, index=True)
    seq = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    name = Column(String(120), nullable=False, default="")
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    run = relationship("TestRun", back_populates="events")


class AssertionResult(Base):
    __tablename__ = "assertion_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("test_runs.id"), nullable=False, index=True)
    assertion_id = Column(String(80), nullable=False)
    description = Column(Text, nullable=False, default="")
    passed = Column(Boolean, nullable=False)
    expected = Column(Text, nullable=False, default="")
    actual = Column(Text, nullable=False, default="")
    explanation = Column(Text, nullable=False, default="")

    run = relationship("TestRun", back_populates="assertion_results")
