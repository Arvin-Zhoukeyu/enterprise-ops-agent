import json
import time
import uuid
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.observability.recorder import (
    TraceRecorder,
)
from app.observability.trace import (
    AgentRunTrace,
    ToolCallTrace,
)
from app.tools import (
    load_tools,
    tool_registry,
)


SYSTEM_PROMPT = """
You are EnterpriseOps Agent, an AI assistant for
enterprise procurement and operational risk analysis.

Your responsibilities:

- Answer questions using enterprise business tools
  whenever private enterprise data is required.

- Never invent supplier, purchase order, payment,
  delivery, risk event, or ticket information.

- Use tools when an answer depends on the enterprise
  database.

- Do not call enterprise tools when the question is
  purely general knowledge and does not require
  company-specific information.

- Prefer read-only tools whenever possible.

- Do not execute write operations unless the runtime
  explicitly permits them.

- Clearly distinguish enterprise database facts from
  your own analysis.

- If a tool returns no matching data, clearly state
  that no enterprise data was found.

Keep responses concise and business-focused.
"""


class BaselineAgent:

    def __init__(
        self,
        save_traces: bool = True,
    ):

        if not settings.openai_api_key:

            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        load_tools()

        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

        self.model = (
            settings.openai_model
        )

        self.tools = (
            tool_registry.to_openai_tools()
        )

        self.save_traces = save_traces

        self.trace_recorder = (
            TraceRecorder()
        )

        self.last_trace: (
            AgentRunTrace | None
        ) = None

    def run(
        self,
        user_input: str,
    ) -> str:

        trace = AgentRunTrace(
            trace_id=str(uuid.uuid4()),
            user_input=user_input,
        )

        self.last_trace = trace

        start_time = (
            time.perf_counter()
        )

        try:

            response = (
                self.client.responses.create(
                    model=self.model,
                    instructions=SYSTEM_PROMPT,
                    input=user_input,
                    tools=self.tools,
                )
            )

            trace.llm_calls += 1

            self._add_usage(
                trace,
                response,
            )

            max_rounds = 5

            for _ in range(
                max_rounds
            ):

                function_calls = [
                    item
                    for item
                    in response.output
                    if item.type
                    == "function_call"
                ]

                if not function_calls:

                    if not trace.tool_calls:

                        trace.routing = (
                            "DIRECT_RESPONSE"
                        )

                    trace.final_answer = (
                        response.output_text
                    )

                    trace.success = True

                    return (
                        response.output_text
                    )

                trace.routing = (
                    "TOOL_CALL"
                )

                tool_outputs = []

                for function_call in (
                    function_calls
                ):

                    result = (
                        self._execute_tool_call(
                            function_call,
                            trace,
                        )
                    )

                    tool_outputs.append(
                        {
                            "type":
                                "function_call_output",

                            "call_id":
                                function_call.call_id,

                            "output":
                                json.dumps(
                                    result,
                                    ensure_ascii=False,
                                    default=str,
                                ),
                        }
                    )

                response = (
                    self.client.responses.create(
                        model=self.model,

                        instructions=(
                            SYSTEM_PROMPT
                        ),

                        previous_response_id=(
                            response.id
                        ),

                        input=tool_outputs,

                        tools=self.tools,
                    )
                )

                trace.llm_calls += 1

                self._add_usage(
                    trace,
                    response,
                )

            trace.success = False

            trace.error = (
                "maximum_tool_rounds_reached"
            )

            trace.final_answer = (
                "Agent stopped because "
                "the maximum tool-call "
                "rounds were reached."
            )

            return trace.final_answer

        except Exception as exc:

            trace.success = False

            trace.error = str(exc)

            raise

        finally:

            trace.latency_ms = (
                (
                    time.perf_counter()
                    - start_time
                )
                * 1000
            )

            if self.save_traces:

                self.trace_recorder.save(
                    trace
                )

            self._print_trace_summary(
                trace
            )

    def _execute_tool_call(
        self,
        function_call: Any,
        trace: AgentRunTrace,
    ) -> Any:

        tool_name = (
            function_call.name
        )

        raw_arguments = (
            function_call.arguments
        )

        tool_start = (
            time.perf_counter()
        )

        try:

            arguments = json.loads(
                raw_arguments
            )

        except json.JSONDecodeError:

            latency_ms = (
                (
                    time.perf_counter()
                    - tool_start
                )
                * 1000
            )

            tool_trace = ToolCallTrace(
                tool_name=tool_name,
                arguments={},
                permission="UNKNOWN",
                side_effect=False,
                status="FAILED",
                latency_ms=latency_ms,
                error=(
                    "invalid_tool_arguments"
                ),
            )

            trace.tool_calls.append(
                tool_trace
            )

            return {
                "success": False,
                "error":
                    "invalid_tool_arguments",
                "details":
                    raw_arguments,
            }

        tool = tool_registry.get(
            tool_name
        )

        print(
            "\n========== Tool Trace =========="
        )

        print(
            f"[Selected Tool] "
            f"{tool_name}"
        )

        print(
            f"[Permission] "
            f"{tool.permission}"
        )

        print(
            f"[Side Effect] "
            f"{tool.side_effect}"
        )

        print(
            f"[Arguments] "
            f"{arguments}"
        )

        if tool.side_effect:

            latency_ms = (
                (
                    time.perf_counter()
                    - tool_start
                )
                * 1000
            )

            result = {
                "success": False,

                "error":
                    "approval_required",

                "message": (
                    f"Tool {tool_name} "
                    f"changes business state "
                    f"and requires human approval."
                ),
            }

            trace.tool_calls.append(
                ToolCallTrace(
                    tool_name=tool_name,
                    arguments=arguments,
                    permission=(
                        tool.permission
                    ),
                    side_effect=(
                        tool.side_effect
                    ),
                    status=(
                        "BLOCKED"
                    ),
                    latency_ms=(
                        latency_ms
                    ),
                    result=result,
                )
            )

            print(
                "[Status] "
                "BLOCKED_BY_APPROVAL"
            )

            print(
                "================================"
            )

            return result

        try:

            result = (
                tool_registry.execute(
                    tool_name,
                    arguments,
                )
            )

            latency_ms = (
                (
                    time.perf_counter()
                    - tool_start
                )
                * 1000
            )

            trace.tool_calls.append(
                ToolCallTrace(
                    tool_name=tool_name,
                    arguments=arguments,
                    permission=(
                        tool.permission
                    ),
                    side_effect=(
                        tool.side_effect
                    ),
                    status="SUCCESS",
                    latency_ms=(
                        latency_ms
                    ),
                    result=result,
                )
            )

            print(
                f"[Tool Result] "
                f"{str(result)[:1000]}"
            )

            print(
                "[Status] SUCCESS"
            )

            print(
                "================================"
            )

            return result

        except Exception as exc:

            latency_ms = (
                (
                    time.perf_counter()
                    - tool_start
                )
                * 1000
            )

            result = {
                "success": False,
                "error":
                    "tool_execution_failed",
                "details":
                    str(exc),
            }

            trace.tool_calls.append(
                ToolCallTrace(
                    tool_name=tool_name,
                    arguments=arguments,
                    permission=(
                        tool.permission
                    ),
                    side_effect=(
                        tool.side_effect
                    ),
                    status="FAILED",
                    latency_ms=(
                        latency_ms
                    ),
                    result=result,
                    error=str(exc),
                )
            )

            print(
                f"[Status] FAILED"
            )

            print(
                f"[Error] {exc}"
            )

            print(
                "================================"
            )

            return result

    def _add_usage(
        self,
        trace: AgentRunTrace,
        response: Any,
    ) -> None:

        usage = getattr(
            response,
            "usage",
            None,
        )

        if usage is None:
            return

        input_tokens = (
            getattr(
                usage,
                "input_tokens",
                0,
            )
            or 0
        )

        output_tokens = (
            getattr(
                usage,
                "output_tokens",
                0,
            )
            or 0
        )

        total_tokens = (
            getattr(
                usage,
                "total_tokens",
                None,
            )
        )

        if total_tokens is None:

            total_tokens = (
                input_tokens
                + output_tokens
            )

        trace.input_tokens += (
            input_tokens
        )

        trace.output_tokens += (
            output_tokens
        )

        trace.total_tokens += (
            total_tokens
        )

    def _print_trace_summary(
        self,
        trace: AgentRunTrace,
    ) -> None:

        print(
            "\n========== Agent Trace =========="
        )

        print(
            f"[Trace ID] "
            f"{trace.trace_id}"
        )

        print(
            f"[Routing] "
            f"{trace.routing}"
        )

        print(
            f"[Tool Calls] "
            f"{len(trace.tool_calls)}"
        )

        print(
            f"[LLM Calls] "
            f"{trace.llm_calls}"
        )

        print(
            f"[Input Tokens] "
            f"{trace.input_tokens}"
        )

        print(
            f"[Output Tokens] "
            f"{trace.output_tokens}"
        )

        print(
            f"[Total Tokens] "
            f"{trace.total_tokens}"
        )

        print(
            f"[Latency] "
            f"{trace.latency_ms:.2f} ms"
        )

        print(
            f"[Success] "
            f"{trace.success}"
        )

        if trace.error:

            print(
                f"[Error] "
                f"{trace.error}"
            )

        print(
            "================================="
        )