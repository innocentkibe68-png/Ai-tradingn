import json
import os
import requests
import logging

# Configure logging to match the rest of the pipeline
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def build_prompt(evidence: dict) -> str:
    return f"""
You are a senior institutional forex analyst reviewing a EUR/USD trading setup.

Use ONLY the numerical evidence supplied below. 
Do NOT invent prices, indicators, news, or chart information. 
If the evidence is conflicting, stale, or insufficient, you MUST output "NO TRADE".

Numerical evidence:
{json.dumps(evidence, indent=2)}

Return ONLY valid JSON in this exact structure. Do not include markdown formatting (like ```json), just the raw JSON object:

{{
  "direction": "BUY | SELL | NO TRADE",
  "confidence": 0,
  "reason": "Brief, institutional-grade explanation of the primary driver for this decision.",
  "technical_summary": "One sentence summarizing the indicator confluence (e.g., 'RSI overbought, MACD bearish cross, price below EMA 50').",
  "risk_flags": ["List", "specific", "risks", "e.g., 'Low volume', 'Approaching major news', 'Conflicting timeframes'"]
}}

Rules:
1. "direction" must be exactly "BUY", "SELL", or "NO TRADE".
2. "confidence" must be an integer from 0 to 100.
3. If evidence is insufficient for a high-probability setup, "direction" MUST be "NO TRADE" and "confidence" MUST be 0.
"""


def call_model(url: str, api_key: str, model: str, prompt: str, provider: str) -> dict:
    if not api_key:
        logging.warning(f"{provider}: API key not configured. Skipping.")
        return {
            "provider": provider,
            "direction": "NO TRADE",
            "confidence": 0,
            "reason": "API key missing.",
            "technical_summary": "N/A",
            "risk_flags": ["MISSING_API_KEY"]
        }

    if not model:
        logging.warning(f"{provider}: Model name not configured. Skipping.")
        return {
            "provider": provider,
            "direction": "NO TRADE",
            "confidence": 0,
            "reason": "Model name missing.",
            "technical_summary": "N/A",
            "risk_flags": ["MISSING_MODEL_NAME"]
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
                "content": "You are a disciplined, risk-first institutional trading analyst. Return ONLY the requested raw JSON object. No markdown, no explanations outside the JSON."
            },
            {
                "role": "user", 
                "content": prompt
            },
        ],
        "temperature": 0.1, # Low temperature for deterministic, factual analysis
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract content and clean it of potential markdown wrappers
        content = data["choices"][0]["message"]["content"].strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        try:
            review = json.loads(content)
            review["provider"] = provider
            return review
        except json.JSONDecodeError:
            logging.error(f"{provider}: Returned invalid JSON. Raw output: {content[:150]}...")
            return {
                "provider": provider,
                "direction": "NO TRADE",
                "confidence": 0,
                "reason": "Model returned invalid JSON.",
                "technical_summary": "N/A",
                "risk_flags": ["INVALID_MODEL_OUTPUT"],
                "raw_output": content[:200]
            }
            
    except requests.exceptions.RequestException as e:
        logging.error(f"{provider}: Request failed - {e}")
        return {
            "provider": provider,
            "direction": "NO TRADE",
            "confidence": 0,
            "reason": f"API request failed: {str(e)}",
            "technical_summary": "N/A",
            "risk_flags": ["API_FAILURE"]
        }


def review_with_all_models(evidence: dict) -> list:
    # Safety check: Ensure we aren't feeding empty data to the AI
    if not evidence or len(str(evidence)) < 50:
        logging.error("Evidence is empty or too short. Aborting AI review.")
        return [{
            "provider": "System", 
            "direction": "NO TRADE", 
            "confidence": 0, 
            "reason": "Empty evidence provided to AI.", 
            "technical_summary": "N/A",
            "risk_flags": ["EMPTY_EVIDENCE"]
        }]

    prompt = build_prompt(evidence)
    reviews = []

    # 1. Mistral
    reviews.append(call_model(
        MISTRAL_URL,
        os.getenv("MISTRAL_API_KEY"),
        os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
        prompt,
        "Mistral",
    ))

    # 2. Groq
    reviews.append(call_model(
        GROQ_URL,
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        prompt,
        "Groq",
    ))

    # 3. NVIDIA
    reviews.append(call_model(
        NVIDIA_URL,
        os.getenv("NVIDIA_API_KEY"),
        os.getenv("NVIDIA_MODEL", "meta/llama3-70b-instruct"),
        prompt,
        "NVIDIA",
    ))

    return reviews