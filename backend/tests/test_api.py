def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_scenarios_seeded_at_least_10(client):
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 10
    ids = {s["id"] for s in data}
    for required in ["order-status-success", "tool-failure", "prompt-injection", "missing-information"]:
        assert required in ids


def test_get_scenario_and_404(client):
    r = client.get("/api/scenarios/order-status-success")
    assert r.status_code == 200
    assert r.json()["user_message"]
    assert client.get("/api/scenarios/does-not-exist").status_code == 404


def test_successful_run_persists_and_retrieves(client):
    r = client.post("/api/runs", json={"scenario_id": "order-status-success"})
    assert r.status_code == 201
    run = r.json()
    assert run["status"] == "passed"
    assert run["passed_count"] == run["total_count"] and run["total_count"] > 0
    assert run["duration_ms"] is not None and run["duration_ms"] >= 0

    fetched = client.get(f"/api/runs/{run['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == run["id"]
    assert len(fetched.json()["assertions"]) == run["total_count"]


def test_known_failure_tool_failure_on_v1(client):
    # mock-v1 does not handle tool failures gracefully: this MUST fail,
    # with an explanation on the failing assertions.
    r = client.post(
        "/api/runs", json={"scenario_id": "tool-failure", "agent_version_id": "mock-v1"}
    )
    assert r.status_code == 201
    run = r.json()
    assert run["status"] == "failed"
    failed = [a for a in run["assertions"] if not a["passed"]]
    assert failed, "expected at least one failing assertion"
    assert all(a["explanation"] for a in failed)


def test_tool_failure_passes_on_v2(client):
    r = client.post(
        "/api/runs", json={"scenario_id": "tool-failure", "agent_version_id": "mock-v2"}
    )
    assert r.status_code == 201
    assert r.json()["status"] == "passed"


def test_events_are_ordered(client):
    run = client.post("/api/runs", json={"scenario_id": "order-status-success"}).json()
    r = client.get(f"/api/runs/{run['id']}/events")
    assert r.status_code == 200
    seqs = [e["seq"] for e in r.json()]
    assert seqs == sorted(seqs)
    assert seqs[0] == 1
    assert len(seqs) == len(set(seqs)), "seq must be unique"
    assert r.json()[0]["event_type"] == "run_started"


def test_replay_creates_new_run(client):
    original = client.post("/api/runs", json={"scenario_id": "order-status-success"}).json()
    replay = client.post(f"/api/runs/{original['id']}/replay", json={})
    assert replay.status_code == 201
    new_run = replay.json()
    assert new_run["id"] != original["id"]
    assert new_run["replay_of_run_id"] == original["id"]
    # Original untouched
    again = client.get(f"/api/runs/{original['id']}").json()
    assert again["replay_of_run_id"] is None


def test_agent_versions_list_and_create(client):
    versions = client.get("/api/agent-versions").json()
    ids = {v["id"] for v in versions}
    assert {"mock-v1", "mock-v2"} <= ids

    created = client.post(
        "/api/agent-versions",
        json={
            "name": "Mock Support Agent",
            "version": "v3-test",
            "description": "created in tests",
            "config": {"handles_tool_failure_gracefully": True},
        },
    )
    assert created.status_code == 201
    assert created.json()["version"] == "v3-test"
    # Duplicate id rejected
    dup = client.post(
        "/api/agent-versions",
        json={"id": created.json()["id"], "name": "x", "version": "vX"},
    )
    assert dup.status_code == 409


def test_compare_newly_passed(client):
    left = client.post(
        "/api/runs", json={"scenario_id": "tool-failure", "agent_version_id": "mock-v1"}
    ).json()
    right = client.post(
        "/api/runs", json={"scenario_id": "tool-failure", "agent_version_id": "mock-v2"}
    ).json()
    r = client.post(
        "/api/compare", json={"left_run_ids": [left["id"]], "right_run_ids": [right["id"]]}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["newly_passed"] == 1
    assert body["items"][0]["change"] == "newly_passed"

    # Mode B: by agent version also works
    r2 = client.post(
        "/api/compare",
        json={"baseline_agent_version_id": "mock-v1", "candidate_agent_version_id": "mock-v2"},
    )
    assert r2.status_code == 200
    changes = {i["scenario_id"]: i["change"] for i in r2.json()["items"]}
    assert changes.get("tool-failure") == "newly_passed"


def test_run_validation_errors(client):
    assert client.post("/api/runs", json={"scenario_id": "nope"}).status_code == 404
    assert client.post("/api/runs", json={}).status_code == 422
    assert client.get("/api/runs/nope").status_code == 404
    assert client.get("/api/runs/nope/events").status_code == 404


# --- v3 additions ------------------------------------------------------------
def test_writes_require_auth(anon_client):
    assert anon_client.post("/api/runs", json={"scenario_id": "order-status-success"}).status_code == 401
    assert anon_client.post("/api/agent-versions", json={"name": "X", "version": "v9"}).status_code == 401


def test_create_custom_scenario_and_run_it(client):
    r = client.post("/api/scenarios", json={
        "id": "custom-hello", "title": "Custom hello", "description": "d",
        "category": "custom", "user_message": "Hi, where is my order ORD-1001?",
        "expected_outcome": "order_status_provided", "tags": ["custom"],
        "context": {"intent": "order_status"},
        "assertions": [{"id": "a1", "type": "tool_called", "description": "lookup", "tool": "lookup_order"}],
    })
    assert r.status_code == 201, r.text
    assert client.post("/api/scenarios", json={
        "id": "custom-hello", "title": "x", "category": "c",
        "user_message": "hi", "expected_outcome": "x", "assertions": [],
    }).status_code == 409
    run = client.post("/api/runs", json={"scenario_id": "custom-hello"}).json()
    assert run["status"] == "passed"


def test_llm_test_requires_key(client):
    r = client.post("/api/llm/test", json={"provider": "groq"})
    assert r.status_code == 400


def test_workspace_and_schedule_flow(client):
    ws = client.post("/api/workspaces", json={"name": "Team Alpha"}).json()
    assert ws["join_code"]
    joined = client.post("/api/workspaces/join", json={"code": ws["join_code"]}).json()
    assert joined["id"] == ws["id"]
    sched = client.post("/api/schedules", json={
        "name": "Suite check", "agent_version_id": "mock-v1", "workspace_id": ws["id"],
    }).json()
    assert sched["id"]
    result = client.post(f"/api/schedules/{sched['id']}/run").json()
    assert result["ok"] is True
    assert result["total"] >= 20  # 11 original + 12 pack scenarios - custom ones
    alerts = client.get("/api/alerts").json()
    assert isinstance(alerts, list)


def test_billing_dormant_without_keys(client):
    r = client.post("/api/billing/checkout", json={"plan": "pro"})
    assert r.status_code == 503
    plan = client.get("/api/billing/plan").json()
    assert plan["plan"] == "free"


def test_stats_endpoint(client):
    stats = client.get("/api/stats").json()
    assert stats["total_runs"] >= 1
    assert stats["by_day"]


def test_llm_test_maps_provider_errors(client, monkeypatch):
    from app.runner import llm_agent

    def boom(*a, **k):
        raise llm_agent.LLMError("API key rejected by the provider (401). Check the key.")
    monkeypatch.setattr(llm_agent, "test_provider", boom)
    r = client.post("/api/llm/test", json={"provider": "groq"}, headers={"X-LLM-Key": "gsk_bad"})
    assert r.status_code == 401
    assert "rejected" in r.json()["detail"]["message"]
