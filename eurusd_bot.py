import logging
from market_data import get_market_data
from ai_review import review_with_all_models
from consensus import build_consensus
from indicators import ema, rsi, atr, macd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    logging.info("Starting EUR/USD institutional analysis pipeline...")

    try:
        data = get_market_data(symbol="EUR/USD", interval="15min", outputsize=250)
        values = data.get("values", [])
        if not values:
            raise ValueError("No candle data returned from Twelve Data.")
    except Exception as e:
        logging.error(f"Failed to fetch market data: {e}")
        with open("message.txt", "w", encoding="utf-8") as f:
            f.write("PIPELINE ERROR: Failed to fetch market data. Check GitHub Actions logs.")
        return

    # Chronological order (Twelve Data returns newest first)
    candles = list(reversed(values))
    closes = [c["close"] for c in candles]
    current_price = closes[-1]

    ema50 = round(ema(closes, 50), 5)
    ema200 = round(ema(closes, 200), 5)
    rsi14 = round(rsi(closes, 14), 2)
    atr14 = round(atr(candles, 14), 5)
    macd_data = macd(closes)
    high_50 = round(max(c["high"] for c in candles[-50:]), 5)
    low_50 = round(min(c["low"] for c in candles[-50:]), 5)

    if current_price > ema50 > ema200:
        trend = "Uptrend"
    elif current_price < ema50 < ema200:
        trend = "Downtrend"
    else:
        trend = "Consolidation"

    evidence = {
        "current_price": current_price,
        "timeframe": "15min",
        "trend": trend,
        "ema_50": ema50,
        "ema_200": ema200,
        "rsi_14": rsi14,
        "macd": macd_data["macd"],
        "macd_signal": macd_data["signal"],
        "macd_histogram": macd_data["histogram"],
        "atr_14": atr14,
        "range_50_high": high_50,
        "range_50_low": low_50,
    }

    logging.info("Querying AI models...")
    reviews = review_with_all_models(evidence)
    consensus = build_consensus(reviews)

    direction = consensus["direction"]
    if direction == "BUY":
        entry = f"{current_price:.5f}"
        stop_loss = f"{current_price - (atr14 * 1.5):.5f}"
        take_profit = f"{current_price + (atr14 * 3.0):.5f}"
        rr = "1:2"
    elif direction == "SELL":
        entry = f"{current_price:.5f}"
        stop_loss = f"{current_price + (atr14 * 1.5):.5f}"
        take_profit = f"{current_price - (atr14 * 3.0):.5f}"
        rr = "1:2"
    else:
        entry = "N/A"
        stop_loss = "N/A"
        take_profit = "N/A"
        rr = "N/A"

    conf = consensus["confidence"]
    conf_label = "High" if conf >= 75 else "Medium" if conf >= 50 else "Low"

    message = (
        f"Pair: EUR/USD\n"
        f"Trend: {trend}\n"
        f"Signal: {direction}\n"
        f"Entry: {entry}\n"
        f"Stop Loss: {stop_loss}\n"
        f"Take Profit: {take_profit}\n"
        f"Risk:Reward: {rr}\n"
        f"Confidence: {conf_label} ({conf}%)\n"
        f"Agreement: {int(consensus['agreement'] * 100)}%\n"
        f"Timeframe: 15min\n"
        f"Reasons: {consensus['reason']}\n"
        f"News Summary: No news feed connected - verify economic calendar manually.\n"
        f"Technical Summary: RSI {rsi14} | MACD {macd_data['macd']} vs signal {macd_data['signal']} | ATR {atr14} | {consensus['technical_summaries']}\n\n"
        f"Status: MANUAL EXECUTION ONLY - verify chart structure before clicking."
    )

    with open("message.txt", "w", encoding="utf-8") as f:
        f.write(message)
    logging.info("Pipeline complete. Report saved to message.txt.")


if __name__ == "__main__":
    main()