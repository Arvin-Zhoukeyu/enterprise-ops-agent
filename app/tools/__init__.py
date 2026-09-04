from app.tools.registry import (
    tool_registry,
)


def load_tools() -> None:

    import app.tools.order_tools
    import app.tools.risk_tools
    import app.tools.supplier_tools
    import app.tools.ticket_tools
    import app.tools.knowledge_tools


__all__ = [
    "tool_registry",
    "load_tools",
]