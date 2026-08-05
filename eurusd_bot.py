import os
import logging
import json
from market_data import get_market_data
from ai_review import review_with_all_models
from consensus import build_consensus

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --- Simple Technical Indicator Calculators (Pure Python, no extra dependencies) ---

def calculate_ema(closes: list, period: int) -> float:
    if len(closes) < period:
        return closes[-1]
    k = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return round(ema, 5)

def calculate_rsi(closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, period + 1):
        change = closes[-i] - closes[-i - 1]
        if change > 0: gains.append(change)
        else: losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# --- Main Orchestrator ---

def main():
    logging.info("Starting EUR/USD Institutional Analysis Pipeline...")

    # 1. Fetch Data (Need 250 candles for a proper 200 EMA on 15m chart)
    logging.info("Fetching market data from Twelve Data...")
    try:
        data = get_market_data(
            symbol="EUR/USD",
            interval="15min",
            outputsize=250
        )
        values = data.get("values", [])
        if not values:
            raise ValueError("No candle data returned from Twelve Data.")
    except Exception as e:
        logging.error(f"Failed to fetch market data: {e}")
        # Write a failure message so Telegram doesn't stay silent
        with open("message.txt", "w") as f:
            f.write("🚨 PIPELINE ERROR: Failed to fetch market data. Check logs.")
        return

    # 2. Process Data & Calculate Indicators
    logging.info("Calculating indicators and building evidence...")
    # Values are usually returned newest to oldest
    closes = [float(v["close"]) for v in values]
    highs = [float(v["high"]) for v in values]
    lows = [float(v["low"]) for v in values]
    
    current_price = closes[0]
    ema_50 = calculate_ema(closes, 50)
    ema_200 = calculate_ema(closes, 200)
    rsi_14 = calculate_rsi(closes, 14)

    # 3. Build the Evidence Dictionary for the AI
    evidence = {
        "current_price": current_price,
        "timeframe": "15-minute",
        "ema_50": ema_50,
        "ema_200": ema_200,
        "rsi_14": rsi_14,
        "recent_highs": highs[:5],
        "recent_lows": lows[:5],
        "last_10_closes": closes[:10]
    }

    # 4. Run AI Models
    logging.info("Querying AI models (Mistral, Groq, NVIDIA)...")
    reviews = review_with_all_models(evidence)

    # 5. Build Consensus
    logging.info("Calculating consensus...")
    consensus = build_consensus(reviews)

    # 6. Format and Write the Final Message
    logging.info("Writing final report to message.txt...")
    message = (
        f"📊 *EUR/USD Institutional Analysis*\n\n"
        f"💰 *Price:* {current_price}\n"
        f"📈 *EMA 50:* {ema_50} | *EMA 200:* {ema_200}\n"
        f"⚡ *RSI (14):* {rsi_14}\n\n"
        f"🎯 *Direction:* {consensus['direction']}\n"
        f"🎲 *Confidence:* {consensus['confidence']}%\n"
        f" *Agreement:* {int(consensus['agreement'] * 100)}%\n\n"
        f"🧠 *Reasoning:* {consensus['reason']}\n\n"
        f"⚠️ *Risk Flags:* {', '.join(consensus['risk_flags']) if consensus['risk_flags'] else 'None'}"
    )

    with open("message.txt", "w", encoding="utf-8") as f:
        f.write(message)
        
    logging.info("Pipeline complete. Report saved to message.txt.")

if __name__ == "__main__":
    main()