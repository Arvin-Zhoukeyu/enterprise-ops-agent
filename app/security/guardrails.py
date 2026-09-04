SUSPICIOUS_PATTERNS = [
    "ignore previous instructions",
    "ignore system prompt",
    "reveal system prompt",
    "delete all",
    "drop table",
    "disable security",
]


def detect_prompt_injection(
    text: str,
) -> bool:

    normalized = (
        text.lower()
    )

    return any(
        pattern in normalized
        for pattern
        in SUSPICIOUS_PATTERNS
    )


def sanitize_rag_results(
    results: list[dict],
) -> list[dict]:

    safe_results = []

    for result in results:

        content = result.get(
            "content",
            "",
        )

        if detect_prompt_injection(
            content
        ):
            continue

        safe_results.append(
            result
        )

    return safe_results