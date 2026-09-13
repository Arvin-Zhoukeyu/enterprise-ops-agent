from pydantic import BaseModel

from app.llm.client import parse_json_object
from app.tools.base import ToolDefinition
from app.tools.registry import ToolRegistry


class ExampleInput(BaseModel):
    supplier_code: str


def test_parse_json_object_from_markdown_fence():
    content = """```json
{"intent": "supplier_lookup", "requires_tools": true}
```"""

    assert parse_json_object(content) == {
        "intent": "supplier_lookup",
        "requires_tools": True,
    }


def test_parse_json_object_with_model_preamble():
    content = (
        "Here is the requested JSON:\n"
        '{"status": "PASS", "reason": "complete"}'
    )

    assert parse_json_object(content)["status"] == "PASS"


def test_chat_completion_tool_schema():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_supplier",
            description="Get one supplier.",
            input_model=ExampleInput,
            handler=lambda supplier_code: supplier_code,
        )
    )

    tools = registry.to_chat_completion_tools()

    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "get_supplier"
    assert (
        tools[0]["function"]["parameters"]
        ["properties"]["supplier_code"]["type"]
        == "string"
    )
    assert "name" not in tools[0]
