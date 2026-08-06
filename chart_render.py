import logging
from pathlib import Path
import pandas as pd
import mplfinance as mpf
from market_data import get_market_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def render_local_chart(output_path="evidence/eurusd_local_chart.png"):
    Path("evidence").mkdir(parents=True, exist_ok=True)

    data = get_market_data(symbol="EUR/USD", interval="15min", outputsize=120)
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    df = df[["open", "high", "low", "close"]].astype(float)

    last_error = None
    for plot_type in ("candles", "candle", "ohlc", "line"):
        try:
            mpf.plot(
                df,
                type=plot_type,
                mav=(20, 50),
                style="charles",
                title="EUR/USD 15m - Desk-Rendered Evidence",
                ylabel="Price",
                figsize=(16, 9),
                savefig=output_path,
            )
            logger.info(f"Chart rendered with type={plot_type}")
            return
        except TypeError as e:
            last_error = e
            logger.warning(f"type={plot_type} rejected; trying next...")

    raise RuntimeError(f"All plot types rejected by mplfinance: {last_error}")


if __name__ == "__main__":
    render_local_chart()