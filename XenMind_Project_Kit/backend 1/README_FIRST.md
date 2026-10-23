# XenMind — Project Kit

**Working brand:** XenMind (verify name/domain/trademark before launch)  
**Product:** AI Agent Reliability Platform  
**Tagline:** Break it. Trace it. Trust it.

## What to give each tool
1. **Lovable:** Upload `XenMind_Product_Spec.md`, then paste `prompts/01_LOVABLE_FRONTEND_PROMPT.md`.
2. **Muse:** Upload `XenMind_Product_Spec.md`, then paste `prompts/02_MUSE_BACKEND_PROMPT.md`. Adapt to Muse's actual capabilities.
3. **Claude:** Upload `XenMind_Product_Spec.md` and `prompts/03_CLAUDE_BUILD_PARTNER_PROMPT.md`. Ask it to work in small, testable steps.

## Build order
1. Create frontend shell and design system in Lovable.
2. Build backend API and deterministic test runner.
3. Connect frontend to the real API.
4. Add traces, replay, scenario reruns, and comparison.
5. Add tests, deployment, README, and demo data.
6. Add auth, billing, and real provider integrations only after the MVP is stable.

## Rules
- Build a real MVP, not a fake demo. Never invent metrics or pretend tests succeeded.
- Start with a deterministic mock agent and mock tools. Add a real model provider later.
- Keep secrets server-side. Never expose API keys in frontend code.
- Do not execute arbitrary user code or call real external tools in the first MVP.
- Inspect existing project files before changing or overwriting them.
