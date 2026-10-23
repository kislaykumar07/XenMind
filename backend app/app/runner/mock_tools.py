"""Deterministic mock tools. No real services, no side effects beyond
returning in-memory data. The same input always gives the same output."""
import hashlib


class ToolError(Exception):
    pass


MOCK_ORDERS = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "status": "shipped",
        "item": "Wireless Headphones",
        "eta": "2 days",
        "tracking": "TRK-1001",
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "status": "delivered",
        "item": "Mechanical Keyboard",
        "eta": "delivered",
        "tracking": "TRK-1002",
    },
}

HELP_CENTER = [
    {
        "id": "returns",
        "title": "How to return an item",
        "keywords": ["return", "refund", "exchange", "send back"],
        "body": "To return an item: 1) Open Orders, 2) Choose the item, 3) Select Return, "
        "4) Print the label and drop the package within 14 days.",
    },
    {
        "id": "shipping",
        "title": "Shipping times",
        "keywords": ["shipping", "delivery", "how long", "arrive"],
        "body": "Standard shipping takes 3-5 business days. Express takes 1-2 business days.",
    },
    {
        "id": "password",
        "title": "Reset your password",
        "keywords": ["password", "login", "sign in", "forgot"],
        "body": "Use Forgot Password on the sign-in page and follow the email link within 30 minutes.",
    },
]


def lookup_order(order_id: str, force_failure: bool = False) -> dict:
    if force_failure or order_id == "ORD-FAIL":
        raise ToolError("lookup_order service unavailable (simulated tool failure)")
    order = MOCK_ORDERS.get(order_id)
    if not order:
        return {"found": False, "order_id": order_id}
    return {"found": True, **order}


def search_help_center(query: str) -> dict:
    q = (query or "").lower()
    matches = [a for a in HELP_CENTER if any(k in q for k in a["keywords"])]
    return {"query": query, "count": len(matches), "results": matches}


def create_support_ticket(subject: str, description: str = "") -> dict:
    digest = hashlib.sha256(f"{subject}|{description}".encode()).hexdigest()[:6].upper()
    return {"ticket_id": f"TICKET-{digest}", "subject": subject, "status": "open"}
