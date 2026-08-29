import json
from dataclasses import asdict
from pathlib import Path

from app.observability.trace import (
    AgentRunTrace,
)


class TraceRecorder:

    def __init__(
        self,
        output_file: str = (
            "outputs/traces/agent_traces.jsonl"
        ),
    ):

        self.output_file = Path(
            output_file
        )

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        trace: AgentRunTrace,
    ) -> None:

        data = asdict(trace)

        with self.output_file.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )