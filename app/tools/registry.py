import json
from typing import Any

from pydantic import (
    BaseModel,
    ValidationError,
)

from app.tools.base import ToolDefinition


class ToolNotFoundError(Exception):
    pass


class ToolValidationError(Exception):
    pass


class ToolRegistry:

    def __init__(self):

        self._tools: dict[
            str,
            ToolDefinition,
        ] = {}

    def register(
        self,
        tool: ToolDefinition,
    ) -> None:

        if tool.name in self._tools:

            raise ValueError(
                f"Tool already registered: "
                f"{tool.name}"
            )

        self._tools[
            tool.name
        ] = tool

    def get(
        self,
        name: str,
    ) -> ToolDefinition:

        tool = self._tools.get(name)

        if tool is None:

            raise ToolNotFoundError(
                f"Unknown tool: {name}"
            )

        return tool

    def list_tools(
        self,
    ) -> list[ToolDefinition]:

        return list(
            self._tools.values()
        )

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:

        tool = self.get(name)

        try:

            validated = (
                tool.input_model
                .model_validate(arguments)
            )

        except ValidationError as exc:

            raise ToolValidationError(
                str(exc)
            ) from exc

        return tool.handler(
            **validated.model_dump()
        )

    def to_openai_tools(
            self,
    ) -> list[dict]:

        tools = []

        for tool in self.list_tools():
            parameters = (
                tool.input_model
                .model_json_schema()
            )

            tools.append(
                {
                    "type": "function",

                    "name": tool.name,

                    "description":
                        tool.description,

                    "parameters":
                        parameters,

                    "strict": False,
                }
            )

        return tools


tool_registry = ToolRegistry()