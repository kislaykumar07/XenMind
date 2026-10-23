# Lovable Prompt — XenMind Frontend

Build the frontend for **XenMind**, a working-name AI Agent Reliability Lab. Read `XenMind_Product_Spec.md` first and follow it as the source of truth.

## Goal
Create a premium, distinctive, responsive developer SaaS interface for testing AI agents, inspecting execution traces, replaying failures, and comparing runs. The core interaction is a visual timeline of a real test run—not a generic chatbot.

## Brand and design
- Brand: XenMind.
- Tagline: “Break it. Trace it. Trust it.”
- Descriptor: “AI Agent Reliability Lab”.
- Dark-first, deep navy/charcoal surfaces, electric violet and cyan accents.
- Abstract X mark inspired by branching execution paths; do not copy existing logos.
- Crisp borders, clean typography, restrained glow, subtle functional motion.
- Accessible contrast, keyboard focus, reduced-motion support, mobile responsiveness.
- Avoid fake metrics, fake customer logos, excessive glassmorphism, and generic AI gradients everywhere.

## Screens
1. Landing page with hero, “Run a demo test” CTA, product preview, benefits, workflow.
2. Lab dashboard with recent runs and actual outcomes.
3. Scenario library with category filters, detail, and run actions.
4. Run detail with event timeline, event inspector, assertion results, replay.
5. Run comparison showing baseline/new outcomes and changed scenarios.
6. Agent versions with labels and prompt/config diffs.
7. Loading, empty, error, and no-data states.

## Interaction and integration
- Make navigation and prototype interactions work.
- Clearly label seeded data as “Demo data” until backend is connected.
- Never pretend a test ran when it did not.
- Put API calls in a dedicated service layer.
- Use TypeScript types for Scenario, AgentVersion, TestRun, RunEvent, and AssertionResult.
- Configure API base URL via environment variable, e.g. `VITE_API_BASE_URL=http://localhost:8000` if compatible.
- Implement API loading/error/empty/success states.
- Never put provider API keys in frontend.
- Do not build billing or real external integrations in the first pass.

## Signature run-detail experience
- Chronological event timeline with event types and statuses.
- Selecting an event opens details.
- Assertions show expected vs actual.
- Replay requests a new run from the backend.
- Comparison highlights changed outcomes.
- Visualizations use actual backend results after integration.

## Workflow
1. Inspect existing project before changing files.
2. Implement design system and app shell first.
3. Build pages in small increments with reusable components.
4. Do not overwrite working code without explaining why.
5. After each stage, summarize files changed, functionality, and how to test.
6. Ask before adding paid dependencies/services.

Start by proposing the frontend structure, then implement the landing page and dashboard shell. Do not generate the whole product in one pass.
