import os
import logging
from market_data import get_market_data
from ai_review import review_with_all_models
from consensus import build_consensus
from indicators import ema, rsi, atr, macd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main():
    logging.info("Starting EUR/USD Institutional Analysis Pipeline...")

    # 1. Fetch Data (250 candles for 200 EMA + MACD)
    try:
        data = get_market_data(symbol="EUR/USD", interval="15min", outputsize=250)
        values = data.get("values", [])
        if not values:
            raise ValueError("No candle data returned from Twelve Data.")
    except Exception as e:
        logging.error(f"Failed to fetch market data: {e}")
        with open("message.txt", "w", encoding="utf-8") as f:
            f.write("🚨 *PIPELINE ERROR*\n\nFailed to fetch market data. Check GitHub Actions logs.")
        return

    # 2. Process Data & Calculate Indicators
    closes = [float(v["close"]) for v in values]
    current_price = closes[0]
    
    ema_50_val = ema(closes, 50)
    ema_200_val = ema(closes, 200)
    rsi_14_val = rsi(closes, 14)
    atr_14_val = atr(values, 14)
    macd_data = macd(closes)

    # Determine Trend programmatically for the AI context
    trend = "Uptrend" if current_price > ema_50_val > ema_200_val else "Downtrend" if current_price < ema_50_val < ema_200_val else "Consolidation"

    # 3. Build Evidence Dictionary for AI
    evidence = {
        "current_price": current_price,
        "timeframe": "15min",
        "trend": trend,
        "ema_50": ema_50_val,
        "ema_200": ema_200_val,
        "rsi_14": rsi_14_val,
        "macd": macd_data["macd"],
        "macd_signal": macd_data["signal"],
        "macd_histogram": macd_data["histogram"],
        "atr_14": atr_14_val
    }

    # 4. Run AI Models & Build Consensus
    reviews = review_with_all_models(evidence)
    consensus = build_consensus(reviews)

    # 5. Calculate Institutional Risk Parameters (ATR-based)
    direction = consensus["direction"]
    if direction == "BUY":
        entry = current_price
        sl = current_price - (atr_14_val * 1.5)
        tp = current_price + (atr_14_val * 3.0)
        rr = "1:2"
    elif direction == "SELL":
        entry = current_price
        sl = current_price + (atr_14_val * 1.5)
        tp = current_price - (atr_14_val * 3.0)
        rr = "1:2"
    else:
        entry = "N/A"
        sl = "N/A"
        tp = "N/A"
        rr = "N/A"

    # 6. Format the Exact Message Template Requested
    confidence_str = "High" if consensus["confidence"] >= 75 else "Medium" if consensus["confidence"] >= 50 else "Low"
    
    message = (
        f"*Pair:* EUR/USD\n"
        f"*Trend:* {trend}\n"
        f"*Signal:* {direction}\n"
        f"*Entry:* {entry if isinstance(entry, str) else f'{entry:.5f}'}\n"
        f"*Stop Loss:* {sl if isinstance(sl, str) else f'{sl:.5f}'}\n"
        f"*Take Profit:* {tp if isinstance(tp, str) else f'{tp:.5f}'}\n"
        f"*Risk:Reward:* {rr}\n"
        f"*Confidence:* {confidence_str} ({consensus['confidence']}%)\n"
        f"*Timeframe:* 15min\n"
        f"*Reasons:* {consensus['reason']}\n"
        f"*News Summary:* Manual check required (Economic Calendar)\n"
        f"*Technical Summary:* RSI ({rsi_14_val}), MACD ({macd_data['macd']:.4f} / Signal: {macd_data['signal']:.4f}), ATR ({atr_14_val:.5f}). {consensus.get('technical_summary', '')}\n\n"
        f"⚠️ *Status:* MANUAL EXECUTION ONLY. Verify chart structure before clicking."
    )

    # 7. Write to file for Telegram to read
    with open("message.txt", "w", encoding="utf-8") as f:
        f.write(message)
        
    logging.info("Pipeline complete. Report saved to message.txt.")

if __name__ == "__main__":
    main()