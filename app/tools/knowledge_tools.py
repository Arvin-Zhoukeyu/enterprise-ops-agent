from pydantic import (
    BaseModel,
    Field,
)

from app.rag.retriever import (
    search_policy,
)
from app.tools.base import (
    ToolDefinition,
)
from app.tools.registry import (
    tool_registry,
)
from app.security.guardrails import (
    sanitize_rag_results,
)

class SearchPolicyInput(
    BaseModel
):

    query: str = Field(
        min_length=3,
        description=(
            "Question or topic to search "
            "within enterprise procurement, "
            "supplier and operational risk "
            "policies."
        ),
    )

    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
    )


def handle_search_policy(
    query: str,
    top_k: int = 4,
) -> list[dict]:

    results = search_policy(
        query=query,
        top_k=top_k,
    )

    return sanitize_rag_results(
        results
    )


tool_registry.register(
    ToolDefinition(
        name="search_enterprise_policy",

        description=(
            "Search enterprise procurement, "
            "supplier risk and operational "
            "risk policies. Use this when "
            "business decisions depend on "
            "company policy or SOP rules."
        ),

        input_model=(
            SearchPolicyInput
        ),

        handler=(
            handle_search_policy
        ),

        permission="READ",

        side_effect=False,
    )
)