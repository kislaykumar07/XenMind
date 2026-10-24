import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.models import AgentVersion, RunEvent, Scenario, TestRun
from app.schemas.schemas import (
    AgentVersionCreate,
    AgentVersionOut,
    CompareItem,
    CompareRequest,
    CompareResponse,
    ReplayRequest,
    RunCreate,
    RunDetail,
    RunEventOut,
    RunOut,
    ScenarioDetail,
    ScenarioOut,
)
from app.services.runner_service import execute_run, get_default_agent

router = APIRouter(prefix="/api")


def _not_found(what: str):
    raise HTTPException(status_code=404, detail={"code": f"{what}_not_found", "message": f"{what} not found"})


def _run_detail(run: TestRun) -> RunDetail:
    base = RunOut.model_validate(run).model_dump()
    return RunDetail(
        **base,
        assertions=[
            {
                "assertion_id": a.assertion_id,
                "description": a.description,
                "passed": a.passed,
                "expected": a.expected,
                "actual": a.actual,
                "explanation": a.explanation,
            }
            for a in sorted(run.assertion_results, key=lambda x: x.id)
        ],
    )


# --- Scenarios -------------------------------------------------------------
@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).order_by(Scenario.id).all()


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        _not_found("scenario")
    return scenario


# --- Agent versions ----------------------------------------------------------
@router.get("/agent-versions", response_model=list[AgentVersionOut])
def list_agent_versions(db: Session = Depends(get_db)):
    return db.query(AgentVersion).order_by(AgentVersion.created_at, AgentVersion.id).all()


@router.post("/agent-versions", response_model=AgentVersionOut, status_code=201)
def create_agent_version(payload: AgentVersionCreate, db: Session = Depends(get_db)):
    version_id = payload.id
    if not version_id:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{payload.name}-{payload.version}".lower()).strip("-")
        version_id = slug[:80] or "agent-version"
    if db.query(AgentVersion).filter(AgentVersion.id == version_id).first():
        raise HTTPException(
            status_code=409, detail={"code": "agent_version_exists", "message": "Agent version id already exists"}
        )
    if payload.is_default:
        db.query(AgentVersion).update({AgentVersion.is_default: False})
    obj = AgentVersion(
        id=version_id,
        name=payload.name,
        version=payload.version,
        description=payload.description,
        config=payload.config,
        is_default=payload.is_default,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Runs --------------------------------------------------------------------
@router.post("/runs", response_model=RunDetail, status_code=201)
def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == payload.scenario_id).first()
    if not scenario:
        _not_found("scenario")
    if payload.agent_version_id:
        agent = db.query(AgentVersion).filter(AgentVersion.id == payload.agent_version_id).first()
        if not agent:
            _not_found("agent_version")
    else:
        agent = get_default_agent(db)
        if not agent:
            raise HTTPException(
                status_code=400, detail={"code": "no_agent_version", "message": "No agent version available"}
            )
    run = execute_run(db, scenario, agent)
    return _run_detail(run)


@router.get("/runs", response_model=list[RunOut])
def list_runs(
    scenario_id: str | None = None,
    agent_version_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(TestRun)
    if scenario_id:
        q = q.filter(TestRun.scenario_id == scenario_id)
    if agent_version_id:
        q = q.filter(TestRun.agent_version_id == agent_version_id)
    if status:
        q = q.filter(TestRun.status == status)
    return q.order_by(TestRun.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        _not_found("run")
    return _run_detail(run)


@router.get("/runs/{run_id}/events", response_model=list[RunEventOut])
def get_run_events(run_id: str, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        _not_found("run")
    return (
        db.query(RunEvent).filter(RunEvent.run_id == run_id).order_by(RunEvent.seq.asc()).all()
    )


@router.post("/runs/{run_id}/replay", response_model=RunDetail, status_code=201)
def replay_run(run_id: str, payload: ReplayRequest | None = None, db: Session = Depends(get_db)):
    original = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not original:
        _not_found("run")
    scenario = db.query(Scenario).filter(Scenario.id == original.scenario_id).first()
    if not scenario:
        _not_found("scenario")
    agent_id = (payload.agent_version_id if payload else None) or original.agent_version_id
    agent = db.query(AgentVersion).filter(AgentVersion.id == agent_id).first()
    if not agent:
        _not_found("agent_version")
    # Replay always creates a NEW run; the original is never modified.
    new_run = execute_run(db, scenario, agent, replay_of_run_id=original.id)
    return _run_detail(new_run)


# --- Compare -------------------------------------------------------------------
@router.post("/compare", response_model=CompareResponse)
def compare(payload: CompareRequest, db: Session = Depends(get_db)):
    left_runs: dict[str, TestRun] = {}
    right_runs: dict[str, TestRun] = {}

    if payload.left_run_ids or payload.right_run_ids:
        for rid in payload.left_run_ids or []:
            run = db.query(TestRun).filter(TestRun.id == rid).first()
            if not run:
                _not_found("run")
            left_runs[run.scenario_id] = run
        for rid in payload.right_run_ids or []:
            run = db.query(TestRun).filter(TestRun.id == rid).first()
            if not run:
                _not_found("run")
            right_runs[run.scenario_id] = run
    elif payload.baseline_agent_version_id and payload.candidate_agent_version_id:
        for version_id, target in [
            (payload.baseline_agent_version_id, left_runs),
            (payload.candidate_agent_version_id, right_runs),
        ]:
            runs = (
                db.query(TestRun)
                .filter(TestRun.agent_version_id == version_id)
                .order_by(TestRun.created_at.asc())
                .all()
            )
            for run in runs:  # later runs overwrite -> latest per scenario wins
                target[run.scenario_id] = run
        if not left_runs and not right_runs:
            raise HTTPException(
                status_code=400,
                detail={"code": "no_runs_to_compare", "message": "No runs found for either agent version"},
            )
    else:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_compare_request",
                "message": "Provide left_run_ids/right_run_ids or baseline/candidate agent version ids",
            },
        )

    scenario_ids = sorted(set(left_runs) | set(right_runs))
    items: list[CompareItem] = []
    summary = {"newly_passed": 0, "newly_failed": 0, "unchanged_passed": 0, "unchanged_failed": 0, "only_left": 0, "only_right": 0}
    for sid in scenario_ids:
        left = left_runs.get(sid)
        right = right_runs.get(sid)
        if left and right:
            if left.status != "passed" and right.status == "passed":
                change = "newly_passed"
            elif left.status == "passed" and right.status != "passed":
                change = "newly_failed"
            elif left.status == "passed" and right.status == "passed":
                change = "unchanged_passed"
            else:
                change = "unchanged_failed"
            summary[change] += 1
        elif left:
            change = "only_left"
            summary["only_left"] += 1
        else:
            change = "only_right"
            summary["only_right"] += 1
        items.append(
            CompareItem(
                scenario_id=sid,
                left_status=left.status if left else None,
                right_status=right.status if right else None,
                change=change,
            )
        )
    return CompareResponse(summary=summary, items=items)
