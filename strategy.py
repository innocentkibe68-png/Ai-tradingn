from typing import List, Dict

from indicators import ema, rsi, atr


def ema_series(values: List[float], period: int) -> List[float]:
    if len(values) < period:
        raise ValueError(f"Need at least {period} values for EMA")

    multiplier = 2 / (period + 1)
    current = sum(values[:period]) / period

    series = [current]

    for price in values[period:]:
        current = (price - current) * multiplier + current
        series.append(current)

    return series


def macd(values: List[float]) -> tuple[float, float]:
    if len(values) < 35:
        raise ValueError("Need at least 35 prices for MACD")

    ema12 = ema_series(values, 12)
    ema26 = ema_series(values, 26)

    # Align EMA12 with EMA26
    offset = len(ema12) - len(ema26)
    macd_line = [
        ema12[i + offset] - ema26[i]
        for i in range(len(ema26))
    ]

    if len(macd_line) < 9:
        raise ValueError("Not enough data for MACD signal")

    signal_series = ema_series(macd_line, 9)

    return macd_line[-1], signal_series[-1]


def generate_signal(candles: List[Dict[str, float]]) -> Dict:
    if len(candles) < 60:
        raise ValueError("Need at least 60 candles for strategy analysis")

    closes = [float(c["close"]) for c in candles]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)
    atr14 = atr(candles, 14)

    macd_line, macd_signal = macd(closes)
    current_price = closes[-1]

    bullish_trend = ema20 > ema50
    bearish_trend = ema20 < ema50

    bullish_momentum = macd_line > macd_signal
    bearish_momentum = macd_line < macd_signal

    if (
        bullish_trend
        and bullish_momentum
        and 50 <= rsi14 < 70
        and current_price > ema20
    ):
        direction = "BUY"

    elif (
        bearish_trend
        and bearish_momentum
        and 30 < rsi14 <= 50
        and current_price < ema20
    ):
        direction = "SELL"

    else:
        direction = "NO TRADE"

    return {
        "direction": direction,
        "price": current_price,
        "ema20": ema20,
        "ema50": ema50,
        "rsi14": rsi14,
        "macd": macd_line,
        "macd_signal": macd_signal,
        "atr14": atr14,
    }