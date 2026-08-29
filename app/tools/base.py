from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass
class ToolDefinition:

    name: str

    description: str

    input_model: type[BaseModel]

    handler: Callable[..., Any]

    permission: str = "READ"

    side_effect: bool = False