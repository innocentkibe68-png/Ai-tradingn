import os
import requests


TELEGRAM_API = "https://api.telegram.org"


def send_telegram_message(message: str) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is not configured.")

    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {data}"
        )


def format_signal_message(
    symbol: str,
    timeframe: str,
    direction: str,
    confidence: float,
    evidence: dict,
) -> str:

    return f"""EUR/USD TRADING ANALYSIS

Symbol: {symbol}
Timeframe: {timeframe}

Signal: {direction}
AI Confidence: {confidence:.1%}

Price: {evidence.get("price", "N/A")}
EMA 20: {evidence.get("ema20", "N/A")}
EMA 50: {evidence.get("ema50", "N/A")}
RSI 14: {evidence.get("rsi14", "N/A")}
MACD: {evidence.get("macd", "N/A")}
MACD Signal: {evidence.get("macd_signal", "N/A")}
ATR 14: {evidence.get("atr14", "N/A")}

Status: MANUAL EXECUTION ONLY
"""


if __name__ == "__main__":
    send_telegram_message(
        "EUR/USD bot test message. Telegram connection is working."
    )