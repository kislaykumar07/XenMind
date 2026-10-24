import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import AgentVersion, AssertionResult, RunEvent, Scenario, TestRun
from app.runner.assertions import evaluate_assertions
from app.runner.llm_agent import LLMError, run_llm_agent
from app.runner.mock_agent import AgentRunResult, run_mock_agent


def get_default_agent(db: Session) -> AgentVersion | None:
    return (
        db.query(AgentVersion).filter(AgentVersion.is_default.is_(True)).first()
        or db.query(AgentVersion).first()
    )


def _persist(
    db: Session,
    scenario: Scenario,
    agent_version: AgentVersion,
    result: AgentRunResult,
    evaluated: list[dict],
    started,
    duration_ms: int,
    replay_of_run_id: str | None,
    workspace_id: str | None,
    agent_kind: str,
    model: str | None,
    status_override: str | None = None,
) -> TestRun:
    finished = datetime.now(timezone.utc)
    passed_count = sum(1 for a in evaluated if a["passed"])
    total = len(evaluated)
    if status_override:
        status = status_override
    else:
        status = "passed" if total > 0 and passed_count == total else "failed"

    run = TestRun(
        id=uuid.uuid4().hex,
        scenario_id=scenario.id,
        agent_version_id=agent_version.id,
        status=status,
        outcome=result.outcome,
        final_response=result.final_response,
        duration_ms=duration_ms,
        passed_count=passed_count,
        total_count=total,
        replay_of_run_id=replay_of_run_id,
        workspace_id=workspace_id,
        agent_kind=agent_kind,
        model=model,
        started_at=started,
        finished_at=finished,
    )
    db.add(run)
    db.flush()

    for ev in result.events:
        db.add(
            RunEvent(
                run_id=run.id,
                seq=ev["seq"],
                event_type=ev["event_type"],
                name=ev["name"],
                payload=ev.get("payload") or {},
            )
        )
    # Ordered assertion events are appended after the agent's own events,
    # keeping seq strictly increasing for the whole run.
    seq = len(result.events)
    for item in evaluated:
        seq += 1
        db.add(
            RunEvent(
                run_id=run.id,
                seq=seq,
                event_type="assertion_check",
                name=item["assertion_id"],
                payload={"passed": item["passed"], "explanation": item["explanation"]},
            )
        )
        db.add(AssertionResult(run_id=run.id, **item))
    db.commit()
    db.refresh(run)
    return run


def execute_run(
    db: Session,
    scenario: Scenario,
    agent_version: AgentVersion,
    replay_of_run_id: str | None = None,
    workspace_id: str | None = None,
    llm_api_key: str | None = None,
) -> TestRun:
    """Run one scenario. LLM versions (config.llm set) use the real LLM agent
    with the caller's key; everything else uses the deterministic mock agent.
    A provider failure persists an honest 'error' run instead of fake data."""
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    config = agent_version.config or {}
    llm_cfg = config.get("llm") if isinstance(config.get("llm"), dict) else None
    if llm_cfg:
        from app.config import settings

        provider = str(llm_cfg.get("provider", "groq")).lower()
        key = llm_api_key or (settings.groq_api_key if provider == "groq" else settings.openai_api_key)
        try:
            result = run_llm_agent(scenario, llm_cfg, api_key=key)
        except LLMError as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            err_result = AgentRunResult(
                final_response=f"LLM provider error: {exc}",
                outcome="llm_error",
                events=[
                    {"seq": 1, "event_type": "run_started", "name": "run_started",
                     "payload": {"scenario_id": scenario.id, "provider": provider}},
                    {"seq": 2, "event_type": "llm_error", "name": "llm_error",
                     "payload": {"error": str(exc)}},
                ],
            )
            return _persist(
                db, scenario, agent_version, err_result, [], started, duration_ms,
                replay_of_run_id, workspace_id, "llm",
                str(llm_cfg.get("model") or ""), status_override="error",
            )
        evaluated = evaluate_assertions(scenario.assertions or [], result)
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return _persist(
            db, scenario, agent_version, result, evaluated, started, duration_ms,
            replay_of_run_id, workspace_id, "llm", str(llm_cfg.get("model") or ""),
        )
    result = run_mock_agent(scenario, config)
    evaluated = evaluate_assertions(scenario.assertions or [], result)
    duration_ms = int((time.perf_counter() - t0) * 1000)
    return _persist(
        db, scenario, agent_version, result, evaluated, started, duration_ms,
        replay_of_run_id, workspace_id, "mock", None,
    )
