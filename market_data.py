import os
import time
import logging
import requests

BASE_URL = "https://api.twelvedata.com/time_series"
logger = logging.getLogger(__name__)


def get_market_data(
    symbol: str = "EUR/USD",
    interval: str = "15min",
    outputsize: int = 250,
    max_retries: int = 3,
):
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        raise RuntimeError("TWELVE_DATA_API_KEY is not set in environment variables.")

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
        "format": "JSON",
    }

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Fetching {symbol} {interval} (attempt {attempt}/{max_retries})...")
            response = requests.get(BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                error_msg = data.get("message", str(data))
                if "rate limit" in error_msg.lower():
                    logger.warning("Rate limit hit. Waiting 5s before retry...")
                    time.sleep(5)
                    continue
                raise RuntimeError(f"Twelve Data API error: {error_msg}")

            for candle in data["values"]:
                candle["open"] = float(candle["open"])
                candle["high"] = float(candle["high"])
                candle["low"] = float(candle["low"])
                candle["close"] = float(candle["close"])
                candle["volume"] = float(candle.get("volume", 0))

            logger.info(f"Fetched {len(data['values'])} candles.")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise RuntimeError(f"Failed to fetch data after {max_retries} attempts: {e}")
            time.sleep(2)

    raise RuntimeError("Failed to fetch market data after all retries.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = get_market_data()
    print("Latest close:", data["values"][0]["close"])