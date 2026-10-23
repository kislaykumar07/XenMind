import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import AgentVersion, AssertionResult, RunEvent, Scenario, TestRun
from app.runner.assertions import evaluate_assertions
from app.runner.mock_agent import run_mock_agent


def get_default_agent(db: Session) -> AgentVersion | None:
    return (
        db.query(AgentVersion).filter(AgentVersion.is_default.is_(True)).first()
        or db.query(AgentVersion).first()
    )


def execute_run(
    db: Session, scenario: Scenario, agent_version: AgentVersion, replay_of_run_id: str | None = None
) -> TestRun:
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    result = run_mock_agent(scenario, agent_version.config or {})
    evaluated = evaluate_assertions(scenario.assertions or [], result)
    duration_ms = int((time.perf_counter() - t0) * 1000)
    finished = datetime.now(timezone.utc)

    passed_count = sum(1 for a in evaluated if a["passed"])
    total = len(evaluated)
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
