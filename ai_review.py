import json
import os
import requests


MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def build_prompt(evidence: dict) -> str:
    return f"""
You are reviewing a EUR/USD trading setup.

Use ONLY the numerical evidence supplied below.
Do not invent prices, indicators, news, or chart information.

Numerical evidence:
{json.dumps(evidence, indent=2)}

Return ONLY valid JSON in this exact structure:

{{
  "direction": "BUY | SELL | NO TRADE",
  "confidence": 0,
  "reason": "brief explanation",
  "risk_flags": []
}}

Rules:
- direction must be BUY, SELL, or NO TRADE
- confidence must be a number from 0 to 1
- do not create entry, SL, or TP values
- do not invent missing information
- if evidence is conflicting or insufficient, use NO TRADE
"""


def call_model(
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    provider: str,
) -> dict:

    if not api_key:
        return {
            "provider": provider,
            "error": "API key not configured"
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a disciplined trading-analysis reviewer. "
                    "Return only the requested JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.1,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    content = data["choices"][0]["message"]["content"].strip()

    try:
        review = json.loads(content)
    except json.JSONDecodeError:
        review = {
            "direction": "NO TRADE",
            "confidence": 0,
            "reason": "Model did not return valid JSON.",
            "risk_flags": ["INVALID_MODEL_OUTPUT"],
            "raw_output": content,
        }

    review["provider"] = provider
    return review


def review_with_all_models(evidence: dict) -> list:
    prompt = build_prompt(evidence)

    reviews = []

    reviews.append(
        call_model(
            MISTRAL_URL,
            os.getenv("MISTRAL_API_KEY"),
            os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
            prompt,
            "Mistral",
        )
    )

    reviews.append(
        call_model(
            GROQ_URL,
            os.getenv("GROQ_API_KEY"),
            os.getenv("GROQ_MODEL"),
            prompt,
            "Groq",
        )
    )

    reviews.append(
        call_model(
            NVIDIA_URL,
            os.getenv("NVIDIA_API_KEY"),
            os.getenv("NVIDIA_MODEL"),
            prompt,
            "NVIDIA",
        )
    )

    return reviews