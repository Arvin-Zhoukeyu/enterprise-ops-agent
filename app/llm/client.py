import json
from typing import Any

from openai import OpenAI

from app.core.config import settings


def create_bailian_client() -> OpenAI:
    if not settings.dashscope_api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY is not configured."
        )

    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        timeout=60.0,
        max_retries=1,
    )


def get_chat_text(response: Any) -> str:
    if not response.choices:
        raise RuntimeError(
            "Bailian returned no completion choices."
        )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Bailian returned an empty message."
        )

    return content.strip()


def parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]

    data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError(
            "Expected the model to return a JSON object."
        )

    return data
