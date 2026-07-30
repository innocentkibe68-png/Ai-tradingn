import os
import requests

BASE_URL = "https://api.twelvedata.com/time_series"


def get_market_data(
    symbol: str = "EUR/USD",
    interval: str = "15min",
    outputsize: int = 100
):
    api_key = os.getenv("TWELVE_DATA_API_KEY")

    if not api_key:
        raise RuntimeError("TWELVE_DATA_API_KEY is not set")

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(
            f"Twelve Data error: {data.get('message', data)}"
        )

    return data


if __name__ == "__main__":
    data = get_market_data()

    print("Symbol:", data["meta"]["symbol"])
    print("Interval:", data["meta"]["interval"])
    print("Latest candle:")
    print(data["values"][0])