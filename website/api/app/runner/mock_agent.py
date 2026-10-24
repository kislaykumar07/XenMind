"""Deterministic mock support agent.

Behaviour is controlled only by the AgentVersion config flags, so two
versions can be compared fairly on the same scenario:

- resists_prompt_injection (bool)
- asks_clarification_when_missing_info (bool)
- handles_tool_failure_gracefully (bool)

No LLM, no randomness, no external calls.
"""
import re

from app.runner.mock_tools import ToolError, create_support_ticket, lookup_order, search_help_center

ORDER_RE = re.compile(r"\b(ORD-[A-Z0-9]+)\b", re.IGNORECASE)

DEFAULT_CONFIG = {
    "resists_prompt_injection": True,
    "asks_clarification_when_missing_info": True,
    "handles_tool_failure_gracefully": False,
}


class AgentRunResult:
    def __init__(self, final_response: str, outcome: str, events: list[dict]):
        self.final_response = final_response
        self.outcome = outcome
        self.events = events


def _cfg(config: dict | None) -> dict:
    merged = dict(DEFAULT_CONFIG)
    if config:
        merged.update(config)
    return merged


def run_mock_agent(scenario, agent_config: dict | None = None) -> AgentRunResult:
    cfg = _cfg(agent_config)
    message: str = scenario.user_message or ""
    context: dict = scenario.context or {}
    intent: str = context.get("intent", "general")
    low = message.lower()
    events: list[dict] = []

    def add(event_type: str, name: str, payload: dict | None = None):
        events.append(
            {"seq": len(events) + 1, "event_type": event_type, "name": name, "payload": payload or {}}
        )

    add("run_started", "run_started", {"scenario_id": scenario.id, "intent": intent})
    add("user_message", "user_message", {"message": message})

    def tool_call(name: str, args: dict):
        add("tool_call", name, {"tool": name, "args": args})

    def tool_result(name: str, result):
        add("tool_result", name, {"tool": name, "result": result})

    def tool_error(name: str, err: str):
        add("tool_error", name, {"tool": name, "error": err})

    def finish(response: str, outcome: str) -> AgentRunResult:
        add("agent_response", "agent_response", {"response": response, "outcome": outcome})
        add("run_completed", "run_completed", {"outcome": outcome})
        return AgentRunResult(response, outcome, events)

    # 1) Prompt-injection-like input
    if intent == "prompt_injection" or "ignore previous" in low or "system prompt" in low:
        if cfg["resists_prompt_injection"]:
            return finish(
                "I can't reveal internal instructions or ignore my guidelines. "
                "I can help you with an order, a return, or another support question instead.",
                "refused_injection",
            )
        return finish(
            "Sure, my system prompt is: you are a helpful agent, always grant a free refund.",
            "leaked_instructions",
        )

    # 2) Unsupported request
    if intent == "unsupported_request":
        return finish(
            "I can't help with that request because it would affect another customer or break policy. "
            "If you have an issue with your own order, I can help or create a support ticket for you.",
            "refused_unsupported",
        )

    # 3) Help-centre search
    if intent == "help_search":
        query = context.get("search_query") or message
        tool_call("search_help_center", {"query": query})
        result = search_help_center(query)
        tool_result("search_help_center", result)
        if result["count"] > 0:
            article = result["results"][0]
            return finish(
                f"Here is how it works: {article['body']}",
                "help_article_provided",
            )
        return finish(
            "I searched the help center and found no article for that topic. "
            "I can create a support ticket so a person can help you.",
            "help_no_results_handled",
        )

    # 4) Ticket / escalation
    if intent == "ticket_creation":
        subject = context.get("ticket_subject") or message[:120]
        tool_call("create_support_ticket", {"subject": subject})
        ticket = create_support_ticket(subject, message)
        tool_result("create_support_ticket", ticket)
        return finish(
            f"I've created a support ticket for you. Your ticket ID is {ticket['ticket_id']}. "
            "Our team will follow up on this issue.",
            "ticket_created",
        )

    # 5) Clarification intents (ambiguity / missing info / invalid format)
    if intent in {"clarification", "missing_information", "invalid_format"}:
        if cfg["asks_clarification_when_missing_info"]:
            if intent == "invalid_format":
                return finish(
                    "That order ID does not look valid. Order IDs look like ORD-1001. "
                    "Could you please share a valid order ID so I can check it?",
                    "asked_clarification",
                )
            return finish(
                "I can help with that. Could you please share your order ID (for example ORD-1001) "
                "and a little more detail about the issue?",
                "asked_clarification",
            )
        # Non-clarifying agent guesses and fails to make progress
        tool_call("lookup_order", {"order_id": ""})
        return finish("I tried to check but I need more details.", "missing_info_unhandled")

    # 6) Order status (default flow, also order_not_found)
    match = ORDER_RE.search(message.upper())
    order_id = match.group(1).upper() if match else context.get("order_id")
    if intent == "order_status" or order_id:
        if not order_id:
            if cfg["asks_clarification_when_missing_info"]:
                return finish(
                    "Could you please share your order ID (for example ORD-1001) so I can track your order?",
                    "asked_clarification",
                )
            return finish("I need an order ID to continue.", "missing_info_unhandled")
        force_failure = bool(context.get("force_tool_failure"))
        tool_call("lookup_order", {"order_id": order_id})
        try:
            result = lookup_order(order_id, force_failure=force_failure)
        except ToolError as exc:
            tool_error("lookup_order", str(exc))
            if cfg["handles_tool_failure_gracefully"]:
                subject = f"Order lookup failed for {order_id}"
                tool_call("create_support_ticket", {"subject": subject})
                ticket = create_support_ticket(subject, message)
                tool_result("create_support_ticket", ticket)
                return finish(
                    f"Sorry, I couldn't look up your order right now because the order system is "
                    f"temporarily unavailable. I've created a support ticket ({ticket['ticket_id']}) "
                    "so our team can check it for you.",
                    "tool_failure_handled",
                )
            return finish(
                f"ToolError: lookup_order failed - {exc}",
                "tool_failure_unhandled",
            )
        tool_result("lookup_order", result)
        if not result.get("found"):
            return finish(
                f"I couldn't find an order with ID {order_id}. Please check the order ID, "
                "or I can create a support ticket if you need more help.",
                "order_not_found",
            )
        return finish(
            f"Your order {result['order_id']} for {result['item']} is {result['status']}. "
            f"Tracking: {result['tracking']}. Expected: {result['eta']}.",
            "order_status_provided",
        )

    # 7) Fallback
    return finish(
        "I can help with order tracking, returns, or creating a support ticket. "
        "Could you tell me a little more about what you need?",
        "asked_clarification",
    )
