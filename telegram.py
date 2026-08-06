import os
import logging
import requests

TELEGRAM_API = "https://api.telegram.org"
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def send_telegram_message(message: str) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is not configured.")

    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    logger.info("Sending message to Telegram...")
    response = requests.post(url, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    logger.info("Message sent successfully.")


if __name__ == "__main__":
    if not os.path.exists("message.txt"):
        raise RuntimeError("message.txt not found - the bot did not produce a report.")
    with open("message.txt", "r", encoding="utf-8") as f:
        send_telegram_message(f.read())