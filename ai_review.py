import json
import os
import requests
import logging

# Configure logging to see what's happening in the GitHub Actions log
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def build_prompt(evidence: dict) -> str:
    return f"""
You are a senior institutional forex analyst reviewing a EUR/USD trading setup.

Use ONLY the numerical evidence supplied below.
Do not invent prices, indicators, news, or chart information.

Numerical evidence:
{json.dumps(evidence, indent=2)}

Return ONLY valid JSON in this exact structure:

{{
  "direction": "BUY | SELL | NO TRADE",
  "confidence": 0,
  "reason": "Brief, institutional-grade explanation based strictly on the evidence.",
  "risk_flags": ["List", "specific", "risks", "e.g., 'Low volume', 'Approaching major news'"]
}}

Rules:
- direction must be exactly "BUY", "SELL", or "NO TRADE".
- confidence must be an integer from 0 to 100.
- If evidence is conflicting, stale, or insufficient, direction MUST be "NO TRADE" and confidence 0.
"""


def call_model(url: str, api_key: str, model: str, prompt: str, provider: str) -> dict:
    if not api_key:
        logging.warning(f"{provider}: API key not configured. Skipping.")
        return {"provider": provider, "direction": "NO TRADE", "confidence": 0, "reason": "API key missing", "risk_flags": ["MISSING_API_KEY"]}

    if not model:
        logging.warning(f"{provider}: Model name not configured. Skipping.")
        return {"provider": provider, "direction": "NO TRADE", "confidence": 0, "reason": "Model name missing", "risk_flags": ["MISSING_MODEL_NAME"]}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a disciplined, risk-first institutional trading analyst. Return ONLY the requested JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        try:
            review = json.loads(content)
            review["provider"] = provider
            return review
        except json.JSONDecodeError:
            logging.error(f"{provider}: Returned invalid JSON. Raw: {content[:100]}...")
            return {
                "provider": provider,
                "direction": "NO TRADE",
                "confidence": 0,
                "reason": "Model returned invalid JSON.",
                "risk_flags": ["INVALID_MODEL_OUTPUT"],
                "raw_output": content[:200] # Truncate to save space
            }
            
    except requests.exceptions.RequestException as e:
        logging.error(f"{provider}: Request failed - {e}")
        return {
            "provider": provider,
            "direction": "NO TRADE",
            "confidence": 0,
            "reason": f"API request failed: {str(e)}",
            "risk_flags": ["API_FAILURE"]
        }


def review_with_all_models(evidence: dict) -> list:
    # Check if evidence is actually populated
    if not evidence or len(str(evidence)) < 50:
        logging.error("Evidence is empty or too short. Aborting AI review.")
        return [{"provider": "System", "direction": "NO TRADE", "confidence": 0, "reason": "Empty evidence provided to AI.", "risk_flags": ["EMPTY_EVIDENCE"]}]

    prompt = build_prompt(evidence)
    reviews = []

    reviews.append(call_model(
        MISTRAL_URL,
        os.getenv("MISTRAL_API_KEY"),
        os.getenv("MISTRAL_MODEL", "mistral-small-latest"), # Safe default
        prompt,
        "Mistral",
    ))

    reviews.append(call_model(
        GROQ_URL,
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_MODEL", "llama3-70b-8192"), # Safe default for Groq
        prompt,
        "Groq",
    ))

    reviews.append(call_model(
        NVIDIA_URL,
        os.getenv("NVIDIA_API_KEY"),
        os.getenv("NVIDIA_MODEL", "meta/llama3-70b-instruct"), # Safe default for NVIDIA
        prompt,
        "NVIDIA",
    ))

    return reviews