from __future__ import annotations
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_MODEL = "gpt-4"


def semantic_spot_check(statement: str, context: str, api_key: str | None = None, model: str | None = None) -> bool:
    """Return True if OpenAI judges the statement supported by the context."""
    api_key = api_key or OPENAI_API_KEY
    if not api_key:
        return False
    try:
        import openai

        resp = openai.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "user", "content": f"Does the following text support the statement: '{statement}'? Answer yes or no.\n{context}"}
            ],
            temperature=0,
            max_tokens=3,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False
