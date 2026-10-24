import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.models import (
    AgentVersion,
    Alert,
    RunEvent,
    Schedule,
    Scenario,
    TestRun,
    UserPlan,
    Workspace,
    WorkspaceMember,
)
from app.schemas.schemas import (
    AgentVersionCreate,
    AgentVersionOut,
    AlertOut,
    AuthResponse,
    BillingCheckoutRequest,
    BillingVerifyRequest,
    CompareItem,
    CompareRequest,
    CompareResponse,
    GoogleAuthRequest,
    LLMTestRequest,
    ReplayRequest,
    RunCreate,
    RunDetail,
    RunEventOut,
    RunOut,
    ScenarioCreate,
    ScenarioDetail,
    ScenarioOut,
    ScheduleCreate,
    ScheduleOut,
    WorkspaceCreate,
    WorkspaceJoin,
    WorkspaceOut,
)
from app.services import auth as auth_svc
from app.services.runner_service import execute_run, get_default_agent

router = APIRouter(prefix="/api")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.client.host if request.client else "unknown") or "unknown"


def _workspace_or_404(db: Session, workspace_id: str, user: dict) -> Workspace:
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        _not_found("workspace")
    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_email == user["email"])
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail={"code": "not_a_member", "message": "Join this workspace first."})
    return ws


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


# --- Auth ------------------------------------------------------------------
@router.post("/auth/google", response_model=AuthResponse)
def google_auth(payload: GoogleAuthRequest):
    info = auth_svc.verify_google_credential(payload.credential)
    token = auth_svc.make_session(info["email"], info["name"], info["picture"])
    return AuthResponse(email=info["email"], name=info["name"], picture=info["picture"], token=token)


# --- Scenarios -------------------------------------------------------------
@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).order_by(Scenario.id).all()


@router.post("/scenarios", response_model=ScenarioDetail, status_code=201)
def create_scenario(payload: ScenarioCreate, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    if db.query(Scenario).filter(Scenario.id == payload.id).first():
        raise HTTPException(status_code=409, detail={"code": "scenario_exists", "message": "Scenario id already exists"})
    for spec in payload.assertions:
        if spec.get("type") not in ("response_contains", "response_not_contains", "tool_called", "tool_not_called", "outcome_is"):
            raise HTTPException(status_code=422, detail={"code": "bad_assertion", "message": f"Unknown assertion type: {spec.get('type')}"})
    obj = Scenario(
        id=payload.id, title=payload.title, description=payload.description,
        category=payload.category, user_message=payload.user_message,
        expected_outcome=payload.expected_outcome, tags=payload.tags,
        context=payload.context, assertions=payload.assertions,
        is_custom=True, created_by=user["email"],
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


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
def create_agent_version(payload: AgentVersionCreate, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
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
def create_run(
    payload: RunCreate,
    request: Request,
    user: dict = Depends(auth_svc.require_user),
    db: Session = Depends(get_db),
    x_llm_key: str | None = Header(default=None),
):
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
    if payload.workspace_id:
        _workspace_or_404(db, payload.workspace_id, user)
    is_llm = isinstance((agent.config or {}).get("llm"), dict)
    auth_svc.rate_limit_run(_client_ip(request), llm=is_llm)
    run = execute_run(db, scenario, agent, workspace_id=payload.workspace_id, llm_api_key=x_llm_key)
    return _run_detail(run)


@router.get("/runs", response_model=list[RunOut])
def list_runs(
    scenario_id: str | None = None,
    agent_version_id: str | None = None,
    status: str | None = None,
    workspace_id: str | None = None,
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
    if workspace_id:
        q = q.filter(TestRun.workspace_id == workspace_id)
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
def replay_run(
    run_id: str,
    request: Request,
    payload: ReplayRequest | None = None,
    user: dict = Depends(auth_svc.require_user),
    db: Session = Depends(get_db),
    x_llm_key: str | None = Header(default=None),
):
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
    is_llm = isinstance((agent.config or {}).get("llm"), dict)
    auth_svc.rate_limit_run(_client_ip(request), llm=is_llm)
    # Replay always creates a NEW run; the original is never modified.
    new_run = execute_run(
        db, scenario, agent, replay_of_run_id=original.id,
        workspace_id=original.workspace_id, llm_api_key=x_llm_key,
    )
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


# --- LLM ---------------------------------------------------------------------
@router.post("/llm/test")
def llm_test(payload: LLMTestRequest, x_llm_key: str | None = Header(default=None)):
    from app.runner.llm_agent import test_provider

    if not x_llm_key:
        raise HTTPException(
            status_code=400,
            detail={"code": "llm_key_required", "message": "Add your provider API key in LLM settings first."},
        )
    from app.runner.llm_agent import LLMError

    try:
        return test_provider(payload.provider, payload.model, x_llm_key)
    except LLMError as exc:
        # Never leak a raw 500 for a provider problem: surface the real cause
        # (bad key, rate limit, bad model) with a matching status code.
        msg = str(exc)
        if "401" in msg or "rejected" in msg:
            status, code = 401, "llm_key_rejected"
        elif "429" in msg or "rate limit" in msg:
            status, code = 429, "llm_rate_limited"
        elif "timed out" in msg:
            status, code = 504, "llm_timeout"
        else:
            status, code = 502, "llm_provider_error"
        raise HTTPException(status_code=status, detail={"code": code, "message": msg})


# --- Stats (for trend charts) --------------------------------------------------
@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    runs = db.query(TestRun).order_by(TestRun.created_at.asc()).limit(2000).all()
    by_day: dict[str, dict[str, int]] = {}
    for r in runs:
        day = (r.created_at or r.started_at).strftime("%Y-%m-%d")
        bucket = by_day.setdefault(day, {"passed": 0, "failed": 0, "error": 0, "total": 0})
        bucket["total"] += 1
        bucket[r.status if r.status in bucket else "failed"] += 1
    per_scenario: dict[str, dict[str, int]] = {}
    for r in runs:
        bucket = per_scenario.setdefault(r.scenario_id, {"passed": 0, "failed": 0, "total": 0})
        bucket["total"] += 1
        if r.status == "passed":
            bucket["passed"] += 1
        elif r.status == "failed":
            bucket["failed"] += 1
    return {
        "by_day": [{"day": d, **v} for d, v in sorted(by_day.items())],
        "per_scenario": [{"scenario_id": s, **v} for s, v in sorted(per_scenario.items())],
        "total_runs": len(runs),
    }


# --- Workspaces ---------------------------------------------------------------
@router.get("/workspaces", response_model=list[WorkspaceOut])
def list_workspaces(user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_email == user["email"]).all()
    out = []
    for m in memberships:
        ws = db.query(Workspace).filter(Workspace.id == m.workspace_id).first()
        if not ws:
            continue
        count = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws.id).count()
        out.append(WorkspaceOut(id=ws.id, name=ws.name, join_code=ws.join_code, role=m.role, member_count=count))
    return out


@router.post("/workspaces", response_model=WorkspaceOut, status_code=201)
def create_workspace(payload: WorkspaceCreate, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    ws_id = "ws-" + uuid.uuid4().hex[:10]
    code = secrets.token_hex(4).upper()
    ws = Workspace(id=ws_id, name=payload.name, join_code=code, created_by=user["email"])
    db.add(ws)
    db.add(WorkspaceMember(workspace_id=ws_id, user_email=user["email"], role="owner"))
    db.commit()
    return WorkspaceOut(id=ws_id, name=payload.name, join_code=code, role="owner", member_count=1)


@router.post("/workspaces/join", response_model=WorkspaceOut)
def join_workspace(payload: WorkspaceJoin, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.join_code == payload.code.strip().upper()).first()
    if not ws:
        _not_found("workspace")
    existing = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_email == user["email"])
        .first()
    )
    if not existing:
        db.add(WorkspaceMember(workspace_id=ws.id, user_email=user["email"], role="member"))
        db.commit()
    count = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws.id).count()
    role = existing.role if existing else "member"
    return WorkspaceOut(id=ws.id, name=ws.name, join_code=ws.join_code, role=role, member_count=count)


# --- Schedules & alerts ---------------------------------------------------------
def _run_schedule(db: Session, sched: Schedule) -> dict:
    agent = db.query(AgentVersion).filter(AgentVersion.id == sched.agent_version_id).first()
    if not agent:
        return {"ok": False, "error": "agent_version_not_found"}
    scenarios = db.query(Scenario).order_by(Scenario.id).all()
    prev = (sched.last_summary or {}).get("items", {})
    newly_failed = 0
    passed = 0
    items: dict[str, str] = {}
    for sc in scenarios:
        run = execute_run(db, sc, agent, workspace_id=sched.workspace_id)
        items[sc.id] = run.status
        if run.status == "passed":
            passed += 1
        if prev.get(sc.id) == "passed" and run.status == "failed":
            newly_failed += 1
            db.add(Alert(schedule_id=sched.id, kind="regression",
                         message=f"Regression in '{sc.title}': passed before, failed now ({agent.name}@{agent.version}).",
                         run_id=run.id))
    sched.last_run_at = datetime.now(timezone.utc)
    sched.last_status = "passed" if newly_failed == 0 else "regression"
    sched.last_summary = {"passed": passed, "total": len(scenarios), "newly_failed": newly_failed, "items": items}
    db.commit()
    if newly_failed > 0 and sched.webhook_url:
        try:
            with httpx.Client(timeout=10.0) as client:
                client.post(sched.webhook_url, json={
                    "text": f"XenMind regression alert: {sched.name} — {newly_failed} scenario(s) newly failed.",
                    "schedule": sched.name, "newly_failed": newly_failed,
                })
        except Exception:
            pass  # webhook failure must not fail the schedule run
    return {"ok": True, "passed": passed, "total": len(scenarios), "newly_failed": newly_failed}


@router.get("/schedules", response_model=list[ScheduleOut])
def list_schedules(user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    return db.query(Schedule).filter(Schedule.created_by == user["email"]).order_by(Schedule.created_at.desc()).all()


@router.post("/schedules", response_model=ScheduleOut, status_code=201)
def create_schedule(payload: ScheduleCreate, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    if not db.query(AgentVersion).filter(AgentVersion.id == payload.agent_version_id).first():
        _not_found("agent_version")
    if payload.workspace_id:
        _workspace_or_404(db, payload.workspace_id, user)
    sched = Schedule(
        id="sch-" + uuid.uuid4().hex[:10], name=payload.name,
        agent_version_id=payload.agent_version_id, workspace_id=payload.workspace_id,
        webhook_url=payload.webhook_url, created_by=user["email"],
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.post("/schedules/{schedule_id}/run")
def run_schedule_now(schedule_id: str, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    sched = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not sched:
        _not_found("schedule")
    if sched.created_by != user["email"]:
        raise HTTPException(status_code=403, detail={"code": "not_owner", "message": "Only the schedule owner can run it."})
    return _run_schedule(db, sched)


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=200)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()


@router.get("/cron/daily")
def cron_daily(request: Request, db: Session = Depends(get_db)):
    """Called by Vercel Cron (see vercel.json) or any external cron service.
    Protected by CRON_SECRET — without it this endpoint is disabled.
    Vercel Cron itself sends `Authorization: Bearer <CRON_SECRET>` when the
    env var is set, so both the header and the ?key= form are accepted."""
    auth = request.headers.get("authorization", "")
    bearer_ok = auth.startswith("Bearer ") and auth[7:].strip() == settings.cron_secret
    key_ok = request.query_params.get("key") == settings.cron_secret
    if not settings.cron_secret or not (bearer_ok or key_ok):
        raise HTTPException(status_code=403, detail={"code": "cron_forbidden", "message": "Cron endpoint disabled or wrong key."})
    results = []
    for sched in db.query(Schedule).filter(Schedule.enabled.is_(True)).all():
        results.append({"schedule_id": sched.id, **_run_schedule(db, sched)})
    return {"ran": len(results), "results": results}


# --- Billing (Razorpay; dormant until keys are configured) ----------------------
PLAN_PRICES = {"pro": 49900, "team": 149900}  # paise


@router.post("/billing/checkout")
def billing_checkout(payload: BillingCheckoutRequest, user: dict = Depends(auth_svc.require_user)):
    if payload.plan not in PLAN_PRICES:
        raise HTTPException(status_code=422, detail={"code": "bad_plan", "message": "Plan must be pro or team."})
    if not (settings.razorpay_key_id and settings.razorpay_key_secret):
        raise HTTPException(
            status_code=503,
            detail={"code": "billing_not_configured", "message": "Billing is not configured yet — this plan stays in preview."},
        )
    with httpx.Client(timeout=20.0, auth=(settings.razorpay_key_id, settings.razorpay_key_secret)) as client:
        resp = client.post("https://api.razorpay.com/v1/orders", json={
            "amount": PLAN_PRICES[payload.plan], "currency": "INR",
            "receipt": f"xm-{payload.plan}-{uuid.uuid4().hex[:8]}",
            "notes": {"plan": payload.plan, "user": user["email"]},
        })
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail={"code": "razorpay_error", "message": f"Razorpay error {resp.status_code}."})
    order = resp.json()
    return {"order_id": order["id"], "key_id": settings.razorpay_key_id,
            "amount": order["amount"], "currency": order["currency"], "plan": payload.plan}


@router.post("/billing/verify")
def billing_verify(payload: BillingVerifyRequest, user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    if not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail={"code": "billing_not_configured", "message": "Billing is not configured yet."})
    msg = f"{payload.order_id}|{payload.payment_id}".encode()
    expect = hmac.new(settings.razorpay_key_secret.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, payload.signature):
        raise HTTPException(status_code=400, detail={"code": "bad_signature", "message": "Payment signature did not verify."})
    plan = db.query(UserPlan).filter(UserPlan.user_email == user["email"]).first()
    # The plan itself is recorded from the checkout receipt note in production;
    # here the verified payment upgrades the caller to Pro (Team via support).
    if not plan:
        plan = UserPlan(user_email=user["email"], plan="pro")
        db.add(plan)
    else:
        plan.plan = "pro"
    db.commit()
    return {"ok": True, "plan": "pro"}


@router.get("/billing/plan")
def billing_plan(user: dict = Depends(auth_svc.require_user), db: Session = Depends(get_db)):
    plan = db.query(UserPlan).filter(UserPlan.user_email == user["email"]).first()
    return {"plan": plan.plan if plan else "free"}
