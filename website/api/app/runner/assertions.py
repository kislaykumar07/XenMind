"""Explicit deterministic assertions.

Supported types (anything else fails with an explanation, never silently):
- response_contains        {value}
- response_not_contains    {value}
- tool_called              {tool}
- tool_not_called          {tool}
- outcome_is               {value}
"""


def _tool_names(events: list[dict]) -> list[str]:
    return [e["name"] for e in events if e.get("event_type") == "tool_call"]


def evaluate_assertions(assertions: list[dict], result) -> list[dict]:
    response_low = (result.final_response or "").lower()
    tools = _tool_names(result.events)
    out: list[dict] = []

    for spec in assertions or []:
        aid = spec.get("id", "assertion")
        atype = spec.get("type", "")
        desc = spec.get("description", aid)
        expected = ""
        actual = ""
        passed = False
        explanation = ""

        if atype == "response_contains":
            value = str(spec.get("value", ""))
            expected = f"response contains '{value}'"
            actual = f"response: {result.final_response[:300]}"
            passed = value.lower() in response_low
            explanation = "Matched." if passed else f"Response did not contain '{value}'."
        elif atype == "response_not_contains":
            value = str(spec.get("value", ""))
            expected = f"response does not contain '{value}'"
            actual = f"response: {result.final_response[:300]}"
            passed = value.lower() not in response_low
            explanation = "Absent as required." if passed else f"Response must not contain '{value}' but it did."
        elif atype == "tool_called":
            tool = str(spec.get("tool", ""))
            expected = f"tool called: {tool}"
            actual = f"tools called: {', '.join(tools) or 'none'}"
            passed = tool in tools
            explanation = "Tool was called." if passed else f"Expected tool '{tool}' was not called."
        elif atype == "tool_not_called":
            tool = str(spec.get("tool", ""))
            expected = f"tool not called: {tool}"
            actual = f"tools called: {', '.join(tools) or 'none'}"
            passed = tool not in tools
            explanation = "Tool was not called." if passed else f"Tool '{tool}' must not be called but it was."
        elif atype == "outcome_is":
            value = str(spec.get("value", ""))
            expected = f"outcome is '{value}'"
            actual = f"outcome: {result.outcome}"
            passed = result.outcome == value
            explanation = "Outcome matched." if passed else f"Expected outcome '{value}', got '{result.outcome}'."
        else:
            expected = f"known assertion type, got '{atype}'"
            actual = atype
            passed = False
            explanation = f"Unknown assertion type '{atype}' - fix the scenario definition."

        out.append(
            {
                "assertion_id": aid,
                "description": desc,
                "passed": passed,
                "expected": expected,
                "actual": actual,
                "explanation": explanation,
            }
        )
    return out
