/* XenMind web app v2 — same-origin adapter for the repo FastAPI backend.
   Contract mirrors frontend/src/lib/api.ts in the GitHub repo:
   backend routes live under /api, snake_case JSON, mapped here.
   v2: Google sign-in gate for the lab, cache-first rendering (no full-page
   loading flashes), custom buttons, subscription plans. */
"use strict";

const API = "/api";
const GOOGLE_CLIENT_ID = "565488602493-f0nopvv1a1jard8v2t0rqe0bsi480us6.apps.googleusercontent.com";

const state = {
  health: null,
  scenarios: [],
  versions: [],
  runs: [],
  runCache: {},       // runId -> { run, events }
  agentSel: "",
  loaded: false,
  refreshing: false,
};

/* ---------------- Auth (Google Identity Services) ---------------- */
const getUser = () => { try { return JSON.parse(localStorage.getItem("xm_user") || "null"); } catch { return null; } };
const setUser = (u) => { if (u) localStorage.setItem("xm_user", JSON.stringify(u)); else localStorage.removeItem("xm_user"); };
const getPlan = () => localStorage.getItem("xm_plan") || "free";
const setPlan = (p) => localStorage.setItem("xm_plan", p);
const parseJwt = (t) => { try { const b = t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"); return JSON.parse(decodeURIComponent(atob(b).split("").map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)).join(""))); } catch { return null; } };

function onGoogleCredential(resp) {
  const p = parseJwt(resp.credential);
  if (!p) { toast("Google sign-in returned an unreadable response. Try again.", "err"); return; }
  setUser({ name: p.name || p.email, email: p.email, picture: p.picture || "" });
  toast(`Welcome, ${(p.name || "there").split(" ")[0]} — you're signed in.`);
  const back = sessionStorage.getItem("xm_return") || "#/lab";
  sessionStorage.removeItem("xm_return");
  if ((location.hash || "#/") === "#/login") location.hash = back; else render();
}
function renderGoogleButtons() {
  if (!(window.google && google.accounts && google.accounts.id)) return;
  document.querySelectorAll(".gbtn-slot").forEach((el) => {
    el.innerHTML = "";
    google.accounts.id.renderButton(el, { theme: "filled_black", size: "large", shape: "pill", text: "continue_with", width: 300 });
  });
}
function initGoogle() {
  if (!(window.google && google.accounts && google.accounts.id)) return;
  google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: onGoogleCredential });
  renderGoogleButtons();
}
function signOut() { setUser(null); toast("Signed out. See you soon."); location.hash = "#/"; }

/* ---------------- API + cache-first data ---------------- */
const $app = document.getElementById("app");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDur = (ms) => (ms == null ? "—" : ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(2)} s`);
const fmtTime = (iso) => { try { return new Date(iso).toLocaleString(); } catch { return iso || ""; } };
const shortId = (id) => (id && id.length > 12 ? id.slice(0, 8) + "…" : id || "");

async function apiGet(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(`Request failed (${r.status})`);
  return r.json();
}
async function apiPost(path, body) {
  const r = await fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) });
  if (!r.ok) { let m = `Request failed (${r.status})`; try { const j = await r.json(); m = (j.detail && (j.detail.message || JSON.stringify(j.detail))) || m; } catch {} throw new Error(m); }
  return r.json();
}
async function fetchCore() {
  const [scenarios, versions, runs] = await Promise.all([
    apiGet("/scenarios"), apiGet("/agent-versions"), apiGet("/runs?limit=200"),
  ]);
  state.scenarios = scenarios; state.versions = versions; state.runs = runs;
  if (!state.agentSel || !versions.some((v) => v.id === state.agentSel)) {
    const def = versions.find((v) => v.is_default) || versions[0];
    state.agentSel = def ? def.id : "";
  }
  state.loaded = true;
}
/* Render instantly from cache; refresh in the background and repaint quietly. */
async function ensureCore() { if (!state.loaded) await fetchCore(); }
function refreshInBackground() {
  if (state.refreshing || !state.loaded) return;
  state.refreshing = true;
  const before = JSON.stringify([state.runs.length, state.runs[0] && state.runs[0].id, state.versions.length]);
  fetchCore().then(() => {
    const after = JSON.stringify([state.runs.length, state.runs[0] && state.runs[0].id, state.versions.length]);
    if (after !== before && !document.querySelector("input:focus, textarea:focus, select:focus")) {
      const y = window.scrollY; render(true); window.scrollTo(0, y);
    }
  }).catch(() => {}).finally(() => { state.refreshing = false; });
}
function refreshHealth() {
  fetch("/health").then((r) => r.json()).then((h) => {
    state.health = h;
    document.querySelectorAll(".live-slot").forEach((el) => { el.innerHTML = liveBadge(); });
  }).catch(() => { state.health = null; });
}
const scenarioName = (id) => { const s = state.scenarios.find((x) => x.id === id); return s ? s.title : id; };
const versionLabel = (id) => { const v = state.versions.find((x) => x.id === id); return v ? `${v.name}@${v.version}` : id; };

function toast(msg, kind) {
  let t = document.getElementById("toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; document.body.appendChild(t); }
  t.textContent = msg;
  t.className = "toast show" + (kind === "err" ? " err" : "");
  clearTimeout(t._h); t._h = setTimeout(() => { t.className = "toast"; }, 3400);
}

const LOGO = `<span class="logo"><svg viewBox="0 0 32 32" style="height:28px;width:28px" aria-hidden="true"><path d="M5 5 L16 16 L27 5" fill="none" stroke="var(--primary)" stroke-width="3" stroke-linecap="round"/><path d="M16 16 L5 27 M16 16 L22 22 L27 27" fill="none" stroke="var(--cyan)" stroke-width="3" stroke-linecap="round"/><circle cx="16" cy="16" r="2.6" fill="var(--foreground)"/><circle cx="22" cy="22" r="1.8" fill="var(--cyan)"/></svg><span>XenMind</span></span>`;
const statusBadge = (s) => s === "passed"
  ? `<span class="badge pass"><span class="dot"></span>Passed</span>`
  : s === "failed" ? `<span class="badge fail"><span class="dot"></span>Failed</span>`
  : `<span class="badge warn"><span class="dot"></span>${esc(s)}</span>`;
const liveBadge = () => state.health
  ? `<span class="badge pass"><span class="dot animate-pulse-dot"></span>Live API</span>`
  : `<span class="badge warn"><span class="dot"></span>API offline</span>`;
const planChip = () => `<span class="plan-chip ${getPlan()}">${esc(getPlan())} plan</span>`;
function userChipHTML() {
  const u = getUser();
  if (!u) return `<a class="btn btn-ghost" href="#/login">Sign in</a><a class="btn btn-primary" href="#/lab">Open lab</a>`;
  return `<span class="user-chip"><img src="${esc(u.picture)}" alt="" referrerpolicy="no-referrer" onerror="this.style.display='none'"/><span>${esc((u.name || u.email || "").split(" ")[0])}</span></span><a class="btn btn-primary" href="#/lab">Open lab</a>`;
}
function busy(btn, label) { btn.disabled = true; btn.dataset.orig = btn.innerHTML; btn.innerHTML = `<span class="spinner"></span> ${label}`; }
function unbusy(btn) { btn.disabled = false; if (btn.dataset.orig) btn.innerHTML = btn.dataset.orig; }

/* ---------------- Landing ---------------- */
const PLANS = [
  { id: "free", name: "Free", price: "₹0", per: "forever", tag: "For trying the lab",
    feats: ["11 seeded scenarios", "Mock agent suite runs", "Step-level traces & replay", "Version compare", "Run history on temporary storage"] },
  { id: "pro", name: "Pro", price: "₹499", per: "/month", tag: "For builders who demo & ship", hot: true,
    feats: ["Everything in Free", "Persistent cloud database — history never resets", "Priority runs — fastest queue, better performance", "Unlimited runs & replays", "Custom scenarios (coming next)", "Email support"] },
  { id: "team", name: "Team", price: "₹1,499", per: "/month", tag: "For teams & classrooms",
    feats: ["Everything in Pro", "5 seats included", "Shared workspaces & run history", "Shared agent versions", "Priority support"] },
];
function plansHTML() {
  const cur = getPlan();
  return `<div class="plans">${PLANS.map((p) => `
    <article class="plan-card ${p.hot ? "hot" : ""}">
      ${p.hot ? `<span class="plan-flag">Most popular</span>` : ""}
      <h3>${p.name}</h3><p class="muted" style="margin:.2rem 0 0;font-size:.85rem">${p.tag}</p>
      <p class="plan-price">${p.price}<span>${p.per}</span></p>
      <ul class="plan-feats">${p.feats.map((f) => `<li>${f}</li>`).join("")}</ul>
      ${cur === p.id
        ? `<button class="btn btn-block" disabled>Current plan</button>`
        : `<button class="btn ${p.hot ? "btn-primary" : "btn-ghost"} btn-block plan-btn" data-plan="${p.id}">${p.id === "free" ? "Downgrade to Free" : "Choose " + p.name}</button>`}
    </article>`).join("")}</div>
  <p class="muted" style="font-size:.8rem;margin-top:1rem">Billing isn't live yet — choosing a plan here is a preview, no payment is taken. Pro performance (persistent database + priority runs) activates when billing opens.</p>`;
}
function bindPlanButtons(root) {
  root.querySelectorAll(".plan-btn").forEach((b) => b.addEventListener("click", () => {
    setPlan(b.dataset.plan);
    toast(b.dataset.plan === "free" ? "You're on the Free plan." : `${b.dataset.plan === "pro" ? "Pro" : "Team"} selected (preview) — billing isn't live yet, no payment taken.`);
    render(true);
  }));
}

function landingHTML() {
  return `
  <div class="wrap view-in">
    <header class="top">${LOGO}<span style="display:flex;gap:.6rem;align-items:center"><span class="live-slot">${liveBadge()}</span>${userChipHTML()}</span></header>
  </div>
  <section class="bg-grid" style="border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
    <div class="wrap hero">
      <div>
        <p class="eyebrow">AI Agent Reliability Lab</p>
        <h1 class="big">Break it. <span class="text-signal">Trace it.</span> Trust it.</h1>
        <p class="lede">Run your agent through hostile scenarios, see every step it took, and know what changed between versions.</p>
        <div style="margin-top:2rem;display:flex;flex-wrap:wrap;gap:.75rem">
          <a class="btn btn-primary btn-lg" href="#/lab">Run a demo test <span class="arr">→</span></a>
          <a class="btn btn-ghost btn-lg" href="#workflow">How it works</a>
        </div>
        <div id="hero-stats" style="margin-top:2.5rem">${state.loaded ? heroStatsHTML() : `<p class="muted"><span class="spinner"></span> Loading live numbers…</p>`}</div>
      </div>
      <div class="card trace-card shadow-glow">
        <div class="trace-head"><span class="mono" style="font-size:.85rem" id="trace-title">Latest real run</span><span id="trace-badge" class="live-slot">${liveBadge()}</span></div>
        <div id="hero-trace">${state.loaded ? "" : `<p class="muted"><span class="spinner"></span> Loading the latest run trace…</p>`}</div>
      </div>
    </div>
  </section>
  <div class="wrap">
    <section class="benefits">
      <div class="card-surface"><h3 style="margin:0;font-weight:600">Scenario tests</h3><p class="muted" style="margin:.5rem 0 0;font-size:.9rem;line-height:1.6">Codify the edge cases that break agents — tool failures, injections, ambiguous asks.</p></div>
      <div class="card-surface"><h3 style="margin:0;font-weight:600">Step-level traces</h3><p class="muted" style="margin:.5rem 0 0;font-size:.9rem;line-height:1.6">Every LLM call, tool call and result on one timeline. Click any step to inspect it.</p></div>
      <div class="card-surface"><h3 style="margin:0;font-weight:600">Replay &amp; compare</h3><p class="muted" style="margin:.5rem 0 0;font-size:.9rem;line-height:1.6">Re-run a failure against a new agent version and see exactly which outcomes changed.</p></div>
    </section>
  </div>
  <section class="band" id="workflow">
    <div class="wrap" style="padding:5rem 1.5rem">
      <h2 style="font-size:1.9rem;font-weight:600;letter-spacing:-.01em;margin:0">The workflow</h2>
      <ol class="steps" style="list-style:none;margin-left:0;padding-left:0">
        ${["Pick a scenario", "Run your agent", "Inspect the trace", "Replay & compare"].map((s, i) => `<li class="step"><span class="mono text-cyan" style="font-size:.72rem">0${i + 1}</span><p style="margin:.3rem 0 0;font-weight:500">${s}</p></li>`).join("")}
      </ol>
      <div style="margin-top:3rem"><a class="btn btn-primary btn-lg" href="#/lab">Open the lab <span class="arr">→</span></a></div>
    </div>
  </section>
  <section class="wrap" id="pricing" style="padding:4.5rem 1.5rem">
    <p class="eyebrow">Subscription</p>
    <h2 style="font-size:1.9rem;font-weight:600;letter-spacing:-.01em;margin:.6rem 0 0">Better performance when you need it</h2>
    <p class="lede" style="margin-top:.8rem">Free is perfect for exploring. Pro keeps your run history forever in a persistent cloud database and puts your runs on the priority queue.</p>
    <div style="margin-top:2rem">${plansHTML()}</div>
  </section>
  <footer class="site">XenMind · working name · Break it. Trace it. Trust it.</footer>`;
}
function heroStatsHTML() {
  const runs = state.runs;
  const passed = runs.filter((r) => r.status === "passed").length;
  return `<div class="stats" style="grid-template-columns:repeat(3,1fr)">
    <div class="stat"><div class="n">${state.scenarios.length}</div><div class="l">Seeded scenarios</div></div>
    <div class="stat"><div class="n">${runs.length}</div><div class="l">Runs recorded</div></div>
    <div class="stat"><div class="n">${runs.length ? Math.round((passed / runs.length) * 100) + "%" : "—"}</div><div class="l">Pass rate (real runs)</div></div>
  </div>`;
}
async function fillHero() {
  const statsEl = document.getElementById("hero-stats");
  const traceEl = document.getElementById("hero-trace");
  if (!statsEl || !traceEl) return;
  try {
    await ensureCore();
    if (!document.getElementById("hero-stats")) return;
    statsEl.innerHTML = heroStatsHTML();
    const latest = state.runs[0];
    if (!latest) {
      traceEl.innerHTML = `<p class="muted">No runs yet on this backend. <a class="text-cyan" href="#/lab">Run the demo</a> and the real trace will appear here.</p>`;
      return;
    }
    document.getElementById("trace-title").textContent = `${shortId(latest.id)} · ${versionLabel(latest.agent_version_id)}`;
    document.getElementById("trace-badge").innerHTML = statusBadge(latest.status);
    const events = await apiGet(`/runs/${latest.id}/events`);
    if (!document.getElementById("hero-trace")) return;
    traceEl.innerHTML = `<p style="margin:0 0 .8rem;font-weight:500">${esc(scenarioName(latest.scenario_id))}</p>` + timelineHTML(events.slice(0, 8)) +
      `<p style="margin:.8rem 0 0"><a class="text-cyan mono" style="font-size:12px" href="#/lab/run/${latest.id}">Open full run →</a></p>`;
  } catch (e) {
    statsEl.innerHTML = `<p class="notice err">Backend unreachable: ${esc(e.message)}</p>`;
    if (traceEl) traceEl.innerHTML = `<p class="muted">The trace loads from the real backend API. It is not reachable right now — nothing here is faked.</p>`;
  }
}

const EVENT_STYLE = {
  run_started: ["violet", ""], user_message: ["", ""], tool_call: ["", ""], tool_result: ["", ""],
  tool_error: ["fail", "fail"], agent_response: ["violet", ""], assertion_check: ["", ""], run_completed: ["violet", ""],
};
function timelineHTML(events) {
  return `<ol class="timeline">${events.map((e) => {
    const isAssert = e.event_type === "assertion_check";
    const failed = e.event_type === "tool_error" || (isAssert && e.payload && e.payload.passed === false);
    const [dot] = EVENT_STYLE[e.event_type] || [""];
    const label = e.event_type === "tool_call" || e.event_type === "tool_result" || e.event_type === "tool_error"
      ? `${e.name} ${e.payload && e.payload.args ? JSON.stringify(e.payload.args) : ""}`
      : e.event_type === "user_message" ? (e.payload.message || e.name)
      : e.event_type === "agent_response" ? (e.payload.response || e.name)
      : isAssert ? `${e.name} — ${e.payload.explanation || ""}`
      : e.name;
    return `<li><span class="tdot ${failed ? "fail" : dot}"></span><div style="min-width:0">
      <p class="ttype">${esc(e.event_type)} · #${e.seq}</p>
      <p class="tlabel ${failed ? "fail" : ""}">${esc(label)}</p>
      <details class="payload"><summary>payload</summary><pre>${esc(JSON.stringify(e.payload, null, 2))}</pre></details>
    </div></li>`;
  }).join("")}</ol>`;
}

/* ---------------- Login ---------------- */
function viewLogin() {
  $app.innerHTML = `<div class="wrap view-in"><header class="top"><a href="#/">${LOGO}</a><a class="btn btn-ghost" href="#/">← Back home</a></header></div>
  <div class="login-wrap">
    <div class="card login-card shadow-glow">
      <div style="display:flex;justify-content:center">${LOGO}</div>
      <h1 style="text-align:center;font-size:1.5rem;margin:1.2rem 0 .4rem">Sign in to the lab</h1>
      <p class="muted" style="text-align:center;margin:0;line-height:1.6;font-size:.95rem">The reliability lab is personal — sign in with Google to run tests, keep your history and compare versions.</p>
      <div class="gbtn-slot" style="display:flex;justify-content:center;margin:1.6rem 0 .4rem;min-height:44px"></div>
      <p class="muted" style="text-align:center;font-size:.78rem;line-height:1.6;margin:.8rem 0 0">If the Google button stays blank or errors, this domain isn't authorised yet — the site owner needs to add <span class="mono">https://xenmind.vercel.app</span> under Authorised JavaScript origins in Google Cloud Console → Credentials.</p>
      <div style="border-top:1px solid var(--border);margin-top:1.4rem;padding-top:1.1rem;display:flex;justify-content:center;gap:.5rem;align-items:center">
        <span class="muted" style="font-size:.85rem">Current plan</span>${planChip()}
      </div>
    </div>
  </div>`;
  initGoogle();
  setTimeout(renderGoogleButtons, 600);
}

/* ---------------- Lab shell ---------------- */
const NAV = [
  ["overview", "#/lab", "Dashboard"], ["scenarios", "#/lab/scenarios", "Scenarios"],
  ["runs", "#/lab/runs", "Test Runs"], ["versions", "#/lab/versions", "Agent Versions"],
  ["compare", "#/lab/compare", "Compare"], ["plan", "#/lab/plan", "Subscription"],
  ["settings", "#/lab/settings", "Settings"],
];
function shellHTML(active, inner) {
  const u = getUser();
  return `<div class="lab view-in">
    <aside class="side"><a href="#/">${LOGO}</a>
      <nav>${NAV.map(([k, href, label]) => `<a href="${href}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>
      <p class="muted" style="font-size:.78rem;margin-top:1.5rem;line-height:1.5">Seeded demo data is labelled. Runs below are real results from this backend.</p>
      ${u ? `<div class="side-user">
        <img src="${esc(u.picture)}" alt="" referrerpolicy="no-referrer" onerror="this.style.display='none'"/>
        <div style="min-width:0"><p class="su-name">${esc(u.name || "")}</p><p class="su-mail">${esc(u.email || "")}</p></div>
        ${planChip()}
        <button class="btn btn-ghost btn-sm" id="btn-signout" style="grid-column:1/-1">Sign out</button>
      </div>` : ""}
    </aside>
    <main class="lab-main">${inner}</main>
  </div>`;
}
function afterShell() { const b = document.getElementById("btn-signout"); if (b) b.addEventListener("click", signOut); }
function noticeHTML(kind, msg) { return msg ? `<p class="notice ${kind || ""}" role="status">${esc(msg)}</p>` : ""; }

/* ---------------- Views (all render instantly from cache) ---------------- */
function viewOverview(notice, kind) {
  const runs = state.runs;
  const passed = runs.filter((r) => r.status === "passed").length;
  const latest = runs[0];
  const inner = `
    <div class="row-head"><div><div style="display:flex;gap:.7rem;align-items:center"><h1 class="page">Dashboard</h1><span class="live-slot">${liveBadge()}</span></div>
    <p class="sub">${runs.length} runs · ${passed} passed · ${runs.length - passed} need attention</p></div>
    <span style="display:flex;gap:.5rem;flex-wrap:wrap">
      <button class="btn btn-ghost" id="btn-suite">Run full suite (${esc(state.agentSel)})</button>
      <a class="btn btn-primary" href="#/lab/scenarios">New test run <span class="arr">→</span></a>
    </span></div>
    <div id="view-notice">${noticeHTML(kind, notice)}</div>
    <div class="stats" style="margin-top:1.5rem">
      <div class="stat"><div class="n">${state.scenarios.length}</div><div class="l">Seeded scenarios</div></div>
      <div class="stat"><div class="n">${state.versions.length}</div><div class="l">Agent versions</div></div>
      <div class="stat"><div class="n">${runs.length}</div><div class="l">Total runs</div></div>
      <div class="stat"><div class="n">${runs.length ? Math.round((passed / runs.length) * 100) + "%" : "—"}</div><div class="l">Pass rate (real runs only)</div></div>
    </div>
    <div class="toolbar"><label class="f" style="margin:0">Agent version for suite runs</label>
      <select id="agent-sel">${state.versions.map((v) => `<option value="${esc(v.id)}" ${v.id === state.agentSel ? "selected" : ""}>${esc(v.name)}@${esc(v.version)}${v.is_default ? " (default)" : ""}</option>`).join("")}</select>
      <span class="muted" style="font-size:.85rem">Known demo story: mock-v1 fails <b>tool-failure</b> on purpose, mock-v2 fixes it.</span></div>
    ${latest ? `<h2 style="margin:2rem 0 0;font-size:1.1rem">Latest run</h2>
    <div class="card" style="margin-top:1rem"><div class="trace-head"><span style="font-weight:500">${esc(scenarioName(latest.scenario_id))}</span>${statusBadge(latest.status)}</div>
    <p class="muted" style="margin:0;font-size:.9rem">${esc(versionLabel(latest.agent_version_id))} · Assertions ${latest.passed_count}/${latest.total_count} · ${fmtDur(latest.duration_ms)} · ${fmtTime(latest.started_at)}</p>
    <p style="margin:.8rem 0 0"><a class="btn btn-sm" href="#/lab/run/${latest.id}">Inspect run</a></p></div>` : ""}
    <h2 style="margin:2rem 0 0;font-size:1.1rem">Recent runs</h2>
    ${runs.length === 0 ? `<div class="empty"><p style="font-weight:500;margin:0">No runs yet</p><p class="sub">Run the full suite or pick a scenario to see real results here.</p></div>` : runsTableHTML(runs.slice(0, 10))}`;
  $app.innerHTML = shellHTML("overview", inner);
  afterShell();
  document.getElementById("agent-sel").addEventListener("change", (e) => { state.agentSel = e.target.value; viewOverview(); });
  document.getElementById("btn-suite").addEventListener("click", async (e) => {
    const btn = e.currentTarget; busy(btn, "Running suite…");
    try { await runSuite(state.agentSel); location.hash = "#/lab/runs"; }
    catch (err) { document.getElementById("view-notice").innerHTML = noticeHTML("err", err.message); unbusy(btn); }
  });
}

function runsTableHTML(runs) {
  return `<div class="tblwrap"><table><thead><tr><th>Status</th><th>Scenario</th><th>Agent</th><th>Assertions</th><th>Duration</th><th>When</th></tr></thead><tbody>
  ${runs.map((r) => `<tr class="clickable" onclick="location.hash='#/lab/run/${r.id}'">
    <td>${statusBadge(r.status)}</td>
    <td><p style="margin:0">${esc(scenarioName(r.scenario_id))}</p><p class="idmono">${esc(shortId(r.id))}${r.replay_of_run_id ? " · replay" : ""}</p></td>
    <td class="mono" style="font-size:12px">${esc(versionLabel(r.agent_version_id))}</td>
    <td class="mono">${r.passed_count}/${r.total_count}</td>
    <td class="mono muted">${fmtDur(r.duration_ms)}</td>
    <td class="muted" style="font-size:.82rem">${fmtTime(r.started_at)}</td></tr>`).join("")}
  </tbody></table></div>`;
}

async function runSuite(agentVersionId) {
  for (const s of state.scenarios) {
    await apiPost("/runs", { scenario_id: s.id, agent_version_id: agentVersionId });
  }
  await fetchCore();
}

function scenarioCardHTML(s) {
  return `
      <article class="scard">
        <div style="display:flex;justify-content:space-between;gap:.5rem;align-items:flex-start"><h3>${esc(s.title)}</h3><span class="badge info">${esc(s.category)}</span></div>
        <p class="muted" style="margin:0;font-size:.88rem;line-height:1.55">${esc(s.description)}</p>
        <p class="msg">"${esc(s.user_message)}"</p>
        <p class="muted" style="margin:0;font-size:.8rem">Expected outcome: <span class="mono">${esc(s.expected_outcome)}</span> · ${s.assertions.length} assertions</p>
        <div style="display:flex;gap:.4rem;flex-wrap:wrap">${(s.tags || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("")}</div>
        <span class="spacer"></span>
        <div><button class="btn btn-run run-btn" data-id="${esc(s.id)}"><span class="tri">▶</span> Run scenario</button></div>
      </article>`;
}
function viewScenarios(notice, kind) {
  const cats = [...new Set(state.scenarios.map((s) => s.category))];
  const inner = `
    <div class="row-head"><div><h1 class="page">Scenario library</h1><p class="sub">${state.scenarios.length} seeded scenarios · deterministic mock tools only · labelled demo data</p></div><span class="live-slot">${liveBadge()}</span></div>
    <div id="view-notice">${noticeHTML(kind, notice)}</div>
    <div class="toolbar">
      <input type="search" id="sc-q" placeholder="Search scenarios…"/>
      <select id="sc-cat"><option value="">All categories</option>${cats.map((c) => `<option>${esc(c)}</option>`).join("")}</select>
      <span class="spacer"></span>
      <label class="f" style="margin:0">Run as</label>
      <select id="agent-sel">${state.versions.map((v) => `<option value="${esc(v.id)}" ${v.id === state.agentSel ? "selected" : ""}>${esc(v.name)}@${esc(v.version)}</option>`).join("")}</select>
    </div>
    <div class="scards" id="sc-grid"></div>`;
  $app.innerHTML = shellHTML("scenarios", inner);
  afterShell();
  const grid = document.getElementById("sc-grid");
  const draw = () => {
    const term = document.getElementById("sc-q").value.toLowerCase();
    const cat = document.getElementById("sc-cat").value;
    const list = state.scenarios.filter((s) => (!cat || s.category === cat) && (!term || (s.title + s.description + s.id).toLowerCase().includes(term)));
    grid.innerHTML = list.map(scenarioCardHTML).join("") || `<p class="muted">No scenarios match.</p>`;
    grid.querySelectorAll(".run-btn").forEach((b) => b.addEventListener("click", async () => {
      busy(b, "Running…");
      try { const run = await apiPost("/runs", { scenario_id: b.dataset.id, agent_version_id: state.agentSel }); await fetchCore(); location.hash = `#/lab/run/${run.id}`; }
      catch (e) { document.getElementById("view-notice").innerHTML = noticeHTML("err", e.message); unbusy(b); }
    }));
  };
  draw();
  document.getElementById("sc-q").addEventListener("input", draw);
  document.getElementById("sc-cat").addEventListener("change", draw);
  document.getElementById("agent-sel").addEventListener("change", (e) => { state.agentSel = e.target.value; });
}

function viewRuns() {
  const inner = `
    <div class="row-head"><div><h1 class="page">Test runs</h1><p class="sub" id="runs-count"></p></div><a class="btn btn-primary" href="#/lab/scenarios">New test run <span class="arr">→</span></a></div>
    <div class="toolbar">
      <select id="f-status"><option value="">Any status</option><option>passed</option><option>failed</option></select>
      <select id="f-ver"><option value="">Any agent version</option>${state.versions.map((v) => `<option value="${esc(v.id)}">${esc(v.name)}@${esc(v.version)}</option>`).join("")}</select>
    </div>
    <div id="runs-body"></div>`;
  $app.innerHTML = shellHTML("runs", inner);
  afterShell();
  const draw = () => {
    const st = document.getElementById("f-status").value;
    const ver = document.getElementById("f-ver").value;
    const list = state.runs.filter((r) => (!st || r.status === st) && (!ver || r.agent_version_id === ver));
    document.getElementById("runs-count").textContent = `${list.length} of ${state.runs.length} runs`;
    document.getElementById("runs-body").innerHTML = list.length === 0
      ? `<div class="empty"><p style="font-weight:500;margin:0">No runs match</p><p class="sub">Run a scenario or the full suite to create real runs.</p></div>`
      : runsTableHTML(list);
  };
  draw();
  document.getElementById("f-status").addEventListener("change", draw);
  document.getElementById("f-ver").addEventListener("change", draw);
}

function runDetailHTML(run, events, notice, kind) {
  const firstFail = (run.assertions || []).find((a) => !a.passed);
  return `
    <p style="margin:0 0 1rem"><a class="muted" href="#/lab/runs">← All runs</a></p>
    <div class="row-head"><div><div style="display:flex;gap:.7rem;align-items:center;flex-wrap:wrap"><h1 class="page">${esc(scenarioName(run.scenario_id))}</h1>${statusBadge(run.status)}</div>
    <p class="sub mono">${esc(run.id)}</p></div>
    <span style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center">
      <select id="replay-ver">${state.versions.map((v) => `<option value="${esc(v.id)}" ${v.id === run.agent_version_id ? "selected" : ""}>${esc(v.name)}@${esc(v.version)}</option>`).join("")}</select>
      <button class="btn btn-primary" id="btn-replay">Replay run</button>
    </span></div>
    <div id="view-notice">${noticeHTML(kind, notice)}</div>
    ${run.replay_of_run_id ? `<p class="notice">This run is a replay of <a class="mono" href="#/lab/run/${esc(run.replay_of_run_id)}">${esc(shortId(run.replay_of_run_id))}</a>. The original was not modified.</p>` : ""}
    <div class="kv" style="margin-top:1.5rem">
      <div><p class="k">Agent version</p><p class="v">${esc(versionLabel(run.agent_version_id))}</p></div>
      <div><p class="k">Outcome (observed)</p><p class="v mono">${esc(run.outcome)}</p></div>
      <div><p class="k">Duration (measured)</p><p class="v">${fmtDur(run.duration_ms)}</p></div>
      <div><p class="k">Started</p><p class="v">${fmtTime(run.started_at)}</p></div>
      <div><p class="k">Assertions</p><p class="v">${run.passed_count}/${run.total_count} passed</p></div>
      <div><p class="k">Scenario</p><p class="v mono">${esc(run.scenario_id)}</p></div>
    </div>
    <h2 style="margin:2rem 0 .7rem;font-size:1.05rem">Agent's final response</h2>
    <div class="response-block">${esc(run.final_response)}</div>
    ${firstFail ? `<div class="fail-first"><p style="margin:0;font-weight:600;color:var(--destructive)">First failing assertion: ${esc(firstFail.assertion_id)}</p>
      <p style="margin:.4rem 0 0;font-size:.9rem">${esc(firstFail.description)} — ${esc(firstFail.explanation)}</p>
      <p class="mono muted" style="margin:.4rem 0 0;font-size:12px">expected: ${esc(firstFail.expected)} · actual: ${esc(firstFail.actual)}</p></div>` : ""}
    <h2 style="margin:2rem 0 .7rem;font-size:1.05rem">Assertions</h2>
    <div class="tblwrap" style="margin-top:0"><table><thead><tr><th>Result</th><th>Assertion</th><th>Expected</th><th>Actual</th><th>Explanation</th></tr></thead><tbody>
    ${(run.assertions || []).map((a) => `<tr><td>${a.passed ? `<span class="badge pass">Pass</span>` : `<span class="badge fail">Fail</span>`}</td>
      <td><p style="margin:0">${esc(a.description)}</p><p class="idmono">${esc(a.assertion_id)}</p></td>
      <td style="font-size:.85rem">${esc(a.expected)}</td><td style="font-size:.85rem">${esc(a.actual)}</td>
      <td style="font-size:.85rem" class="muted">${esc(a.explanation)}</td></tr>`).join("")}
    </tbody></table></div>
    <h2 style="margin:2rem 0 .7rem;font-size:1.05rem">Execution trace</h2>
    <div class="card">${timelineHTML(events)}</div>`;
}
function viewRunDetail(runId, notice, kind) {
  const cached = state.runCache[runId];
  if (!cached) {
    $app.innerHTML = shellHTML("runs", `<div class="card" style="margin-top:1rem"><p class="muted" style="margin:0"><span class="spinner"></span> Loading this run…</p></div>`);
    afterShell();
    Promise.all([apiGet(`/runs/${runId}`), apiGet(`/runs/${runId}/events`)]).then(([run, events]) => {
      state.runCache[runId] = { run, events };
      if (location.hash.includes(runId)) viewRunDetail(runId, notice, kind);
    }).catch((e) => { if (location.hash.includes(runId)) { $app.innerHTML = shellHTML("runs", noticeHTML("err", e.message)); afterShell(); } });
    return;
  }
  $app.innerHTML = shellHTML("runs", runDetailHTML(cached.run, cached.events, notice, kind));
  afterShell();
  document.getElementById("btn-replay").addEventListener("click", async (e) => {
    const btn = e.currentTarget; busy(btn, "Replaying…");
    try {
      const nr = await apiPost(`/runs/${runId}/replay`, { agent_version_id: document.getElementById("replay-ver").value });
      await fetchCore();
      location.hash = `#/lab/run/${nr.id}`;
    } catch (err) { document.getElementById("view-notice").innerHTML = noticeHTML("err", err.message); unbusy(btn); }
  });
}

function viewVersions(notice, kind) {
  const sw = (id, label, help, checked) => `
    <label class="switch-row"><span class="switch"><input type="checkbox" id="${id}" ${checked ? "checked" : ""}/><span class="track"></span></span>
    <span>${label}<small>${help}</small></span></label>`;
  const inner = `
    <div class="row-head"><div><h1 class="page">Agent versions</h1><p class="sub">Behaviour is controlled by config flags — that is what makes versions comparable.</p></div><span class="live-slot">${liveBadge()}</span></div>
    <div id="view-notice">${noticeHTML(kind, notice)}</div>
    <div class="scards">${state.versions.map((v) => `
      <article class="scard">
        <div style="display:flex;justify-content:space-between;gap:.5rem"><h3>${esc(v.name)}@${esc(v.version)}</h3>${v.is_default ? `<span class="badge info">Default</span>` : ""}</div>
        <p class="muted" style="margin:0;font-size:.88rem;line-height:1.55">${esc(v.description || "")}</p>
        <div style="display:flex;gap:.4rem;flex-wrap:wrap">${Object.entries(v.config || {}).map(([k, val]) => `<span class="chip ${val ? "on" : "off"}">${esc(k)}: ${val ? "on" : "off"}</span>`).join("")}</div>
        <p class="muted" style="margin:0;font-size:.8rem">Runs recorded: ${state.runs.filter((r) => r.agent_version_id === v.id).length} · Created ${fmtTime(v.created_at)}</p>
        <div><button class="btn btn-ghost btn-sm suite-btn" data-id="${esc(v.id)}">Run full suite as this version</button></div>
      </article>`).join("")}</div>
    <h2 style="margin:2.5rem 0 0;font-size:1.1rem">Create a new version</h2>
    <form id="ver-form" class="card" style="margin-top:1rem">
      <div class="formgrid">
        <div><label class="f">Name</label><input type="text" id="vf-name" required maxlength="200" value="Mock Support Agent"/></div>
        <div><label class="f">Version label</label><input type="text" id="vf-version" required maxlength="50" placeholder="v3"/></div>
      </div>
      <div style="margin-top:1rem"><label class="f">Description</label><textarea id="vf-desc" rows="2" maxlength="2000" placeholder="What changed in this version?"></textarea></div>
      <div class="formgrid" style="margin-top:1rem">
        ${sw("vf-inj", "Resists prompt injection", "Refuses to reveal internal instructions.", true)}
        ${sw("vf-clar", "Asks for clarification", "When required information is missing.", true)}
        ${sw("vf-tool", "Handles tool failure gracefully", "Apologises and creates a ticket fallback instead of leaking errors.", true)}
        ${sw("vf-def", "Make default", "New runs without a chosen version will use this one.", false)}
      </div>
      <div style="margin-top:1.25rem"><button class="btn btn-primary" type="submit">Create version <span class="arr">→</span></button></div>
    </form>`;
  $app.innerHTML = shellHTML("versions", inner);
  afterShell();
  document.querySelectorAll(".suite-btn").forEach((b) => b.addEventListener("click", async () => {
    busy(b, "Running suite…");
    try { await runSuite(b.dataset.id); location.hash = "#/lab/runs"; } catch (e) { viewVersions(e.message, "err"); }
  }));
  document.getElementById("ver-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]"); busy(btn, "Creating…");
    try {
      await apiPost("/agent-versions", {
        name: document.getElementById("vf-name").value.trim(),
        version: document.getElementById("vf-version").value.trim(),
        description: document.getElementById("vf-desc").value.trim(),
        config: {
          resists_prompt_injection: document.getElementById("vf-inj").checked,
          asks_clarification_when_missing_info: document.getElementById("vf-clar").checked,
          handles_tool_failure_gracefully: document.getElementById("vf-tool").checked,
        },
        is_default: document.getElementById("vf-def").checked,
      });
      await fetchCore();
      viewVersions("Version created. Run the suite as this version, then compare it against an older one.", "ok");
      toast("Agent version created.");
    } catch (err) { viewVersions(err.message, "err"); }
  });
}

function viewCompare(notice, kind, result) {
  const v = state.versions;
  const inner = `
    <div class="row-head"><div><h1 class="page">Compare versions</h1><p class="sub">Uses the latest run per scenario for each version. Run a suite first if a version has no runs.</p></div><span class="live-slot">${liveBadge()}</span></div>
    <div id="view-notice">${noticeHTML(kind, notice)}</div>
    <form id="cmp-form" class="card" style="margin-top:1.5rem">
      <div class="formgrid">
        <div><label class="f">Baseline (older)</label><select id="cmp-left" style="width:100%">${v.map((x) => `<option value="${esc(x.id)}">${esc(x.name)}@${esc(x.version)}</option>`).join("")}</select></div>
        <div><label class="f">Candidate (newer)</label><select id="cmp-right" style="width:100%">${v.map((x, i) => `<option value="${esc(x.id)}" ${i === 1 ? "selected" : ""}>${esc(x.name)}@${esc(x.version)}</option>`).join("")}</select></div>
      </div>
      <div style="margin-top:1.25rem;display:flex;gap:.6rem;flex-wrap:wrap">
        <button class="btn btn-primary" type="submit">Compare latest runs</button>
        <button class="btn btn-ghost" type="button" id="cmp-both">Run suite for both &amp; compare</button>
      </div>
    </form>
    <div id="cmp-result">${result ? compareHTML(result) : ""}</div>`;
  $app.innerHTML = shellHTML("compare", inner);
  afterShell();
  const doCompare = async () => {
    const left = document.getElementById("cmp-left").value, right = document.getElementById("cmp-right").value;
    if (left === right) throw new Error("Pick two different versions to compare.");
    return apiPost("/compare", { baseline_agent_version_id: left, candidate_agent_version_id: right });
  };
  document.getElementById("cmp-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]"); busy(btn, "Comparing…");
    try { const res = await doCompare(); document.getElementById("cmp-result").innerHTML = compareHTML(res); }
    catch (err) { document.getElementById("cmp-result").innerHTML = noticeHTML("err", err.message); }
    unbusy(btn);
  });
  document.getElementById("cmp-both").addEventListener("click", async (e) => {
    const btn = e.currentTarget; busy(btn, "Running both suites…");
    try {
      await runSuite(document.getElementById("cmp-left").value);
      await runSuite(document.getElementById("cmp-right").value);
      const res = await doCompare();
      document.getElementById("cmp-result").innerHTML = compareHTML(res);
    } catch (err) { document.getElementById("cmp-result").innerHTML = noticeHTML("err", err.message); }
    unbusy(btn);
  });
}
function compareHTML(res) {
  const s = res.summary || {};
  const chipFor = (c) => c === "newly_passed" ? `<span class="badge pass">Newly passed</span>` : c === "newly_failed" ? `<span class="badge fail">Newly failed</span>` : c === "unchanged_passed" ? `<span class="badge pass">Still passing</span>` : c === "unchanged_failed" ? `<span class="badge fail">Still failing</span>` : `<span class="badge warn">${esc(c.replaceAll("_", " "))}</span>`;
  return `<div class="stats" style="margin-top:1.5rem">
    <div class="stat"><div class="n" style="color:var(--success)">${s.newly_passed || 0}</div><div class="l">Newly passed</div></div>
    <div class="stat"><div class="n" style="color:var(--destructive)">${s.newly_failed || 0}</div><div class="l">Newly failed</div></div>
    <div class="stat"><div class="n">${s.unchanged_passed || 0}</div><div class="l">Unchanged (passing)</div></div>
    <div class="stat"><div class="n">${s.unchanged_failed || 0}</div><div class="l">Unchanged (failing)</div></div></div>
  <div class="tblwrap"><table><thead><tr><th>Scenario</th><th>Baseline</th><th>Candidate</th><th>Change</th></tr></thead><tbody>
  ${res.items.map((i) => `<tr><td>${esc(scenarioName(i.scenario_id))}<p class="idmono">${esc(i.scenario_id)}</p></td>
    <td>${i.left_status ? statusBadge(i.left_status) : `<span class="muted">no run</span>`}</td>
    <td>${i.right_status ? statusBadge(i.right_status) : `<span class="muted">no run</span>`}</td>
    <td>${chipFor(i.change)}</td></tr>`).join("")}
  </tbody></table></div>`;
}

function viewPlan() {
  const cur = PLANS.find((p) => p.id === getPlan()) || PLANS[0];
  const inner = `
    <div class="row-head"><div><h1 class="page">Subscription</h1><p class="sub">Your plan controls storage and run performance.</p></div>${planChip()}</div>
    <div class="card" style="margin-top:1.5rem">
      <div class="kv">
        <div><p class="k">Current plan</p><p class="v">${esc(cur.name)} · ${esc(cur.price)}${esc(cur.per)}</p></div>
        <div><p class="k">Run history storage</p><p class="v">${getPlan() === "free" ? "Temporary — can reset when the backend restarts" : "Persistent cloud database"}</p></div>
        <div><p class="k">Run queue</p><p class="v">${getPlan() === "free" ? "Standard" : "Priority — better performance"}</p></div>
        <div><p class="k">Billing</p><p class="v">Preview — billing isn't live yet, no payment is taken</p></div>
      </div>
    </div>
    <h2 style="margin:2.2rem 0 0;font-size:1.1rem">Plans</h2>
    <div style="margin-top:1rem">${plansHTML()}</div>
    <h2 style="margin:2.2rem 0 0;font-size:1.1rem">Performance, honestly</h2>
    <div class="tblwrap"><table><thead><tr><th></th><th>Free</th><th>Pro / Team</th></tr></thead><tbody>
      <tr><td>Run history</td><td>Temporary storage — resets possible</td><td>Persistent cloud database — never resets</td></tr>
      <tr><td>Run queue</td><td>Standard</td><td>Priority — better performance</td></tr>
      <tr><td>Runs &amp; replays</td><td>Fair use</td><td>Unlimited</td></tr>
      <tr><td>Support</td><td>Community</td><td>Email / priority</td></tr>
    </tbody></table></div>`;
  $app.innerHTML = shellHTML("plan", inner);
  afterShell();
  bindPlanButtons($app);
}

function viewSettings() {
  const health = state.health;
  const inner = `
    <div class="row-head"><div><h1 class="page">Settings</h1><p class="sub">How this deployment is wired.</p></div></div>
    <div class="card" style="margin-top:1.5rem">
      <div class="kv">
        <div><p class="k">Backend health</p><p class="v">${health ? `${esc(health.status)} · ${esc(health.service)} v${esc(health.version)} · database ${esc(health.database)}` : "checking…"}</p></div>
        <div><p class="k">Signed in as</p><p class="v">${esc((getUser() || {}).email || "—")}</p></div>
        <div><p class="k">Plan</p><p class="v" style="text-transform:capitalize">${esc(getPlan())} (preview — billing not live)</p></div>
        <div><p class="k">API base</p><p class="v mono">same origin · /api</p></div>
        <div><p class="k">OpenAPI docs</p><p class="v"><a class="text-cyan" href="/docs" target="_blank" rel="noopener">/docs</a></p></div>
      </div>
      <h3 style="margin:1.5rem 0 .5rem">Honest limits of this demo deployment</h3>
      <ul class="muted" style="line-height:1.7;font-size:.92rem;margin:0;padding-left:1.2rem">
        <li>The agent is a <b>deterministic mock</b> — no real LLM, no real external tools, no billing. That is deliberate: reliability tests must be repeatable.</li>
        <li>Data lives in the project database: Postgres in production when <span class="mono">DATABASE_URL</span> is configured, SQLite for local development. Scenarios and agent versions are re-seeded automatically on an empty database.</li>
        <li>Sign-in uses Google Identity Services in the browser. The backend does not yet verify ID tokens server-side — add that before a public multi-user release.</li>
        <li>No latency or cost is ever invented: the only timing shown is the measured run duration.</li>
      </ul>
    </div>`;
  $app.innerHTML = shellHTML("settings", inner);
  afterShell();
}

/* ---------------- Router (cache-first, no loading flashes) ---------------- */
function skeletonHTML() {
  return `<div class="lab view-in"><aside class="side"><a href="#/">${LOGO}</a><nav>${NAV.map(([k, href, label]) => `<a href="${href}">${label}</a>`).join("")}</nav></aside>
  <main class="lab-main"><p class="muted" style="margin-top:2rem"><span class="spinner"></span> Loading the lab…</p></main></div>`;
}
async function render(soft) {
  const hash = location.hash || "#/";
  const path = hash.replace(/^#/, "").split("?")[0];
  refreshHealth();
  if (path === "/" || path === "") {
    $app.innerHTML = landingHTML();
    bindPlanButtons($app);
    renderGoogleButtons();
    fillHero();
    if (!soft) window.scrollTo(0, 0);
    return;
  }
  if (path === "/login") {
    if (getUser()) { location.hash = sessionStorage.getItem("xm_return") || "#/lab"; sessionStorage.removeItem("xm_return"); return; }
    viewLogin();
    return;
  }
  if (path.startsWith("/lab")) {
    if (!getUser()) { sessionStorage.setItem("xm_return", hash); location.hash = "#/login"; return; }
    if (!state.loaded) {
      $app.innerHTML = skeletonHTML();
      try { await fetchCore(); }
      catch (e) { $app.innerHTML = shellHTML("", `<div class="notice err" style="margin-top:2rem"><b>Couldn't load the lab.</b><br/>${esc(e.message)}<br/><span class="muted">If the backend just deployed, give it a few seconds and refresh.</span></div>`); afterShell(); return; }
      if ((location.hash || "#/") !== hash) return;
    }
    if (path === "/lab") viewOverview();
    else if (path === "/lab/scenarios") viewScenarios();
    else if (path === "/lab/runs") viewRuns();
    else if (path.startsWith("/lab/run/")) viewRunDetail(path.split("/")[3]);
    else if (path === "/lab/versions") viewVersions();
    else if (path === "/lab/compare") viewCompare();
    else if (path === "/lab/plan") viewPlan();
    else if (path === "/lab/settings") viewSettings();
    else viewOverview();
    if (!soft) window.scrollTo(0, 0);
    refreshInBackground();
    return;
  }
  $app.innerHTML = landingHTML();
  bindPlanButtons($app);
  fillHero();
}
window.addEventListener("hashchange", () => render());
window.addEventListener("load", () => initGoogle());
render();
