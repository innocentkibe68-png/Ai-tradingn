from typing import List, Dict


def ema(values: List[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"Need at least {period} values for EMA")

    multiplier = 2 / (period + 1)
    current_ema = sum(values[:period]) / period

    for price in values[period:]:
        current_ema = (price - current_ema) * multiplier + current_ema

    return current_ema


def rsi(values: List[float], period: int = 14) -> float:
    if len(values) <= period:
        raise ValueError(f"Need more than {period} values for RSI")

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def true_ranges(candles: List[Dict[str, float]]) -> List[float]:
    ranges = []

    for i, candle in enumerate(candles):
        high = candle["high"]
        low = candle["low"]

        if i == 0:
            previous_close = candle["close"]
        else:
            previous_close = candles[i - 1]["close"]

        tr = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close),
        )

        ranges.append(tr)

    return ranges


def atr(candles: List[Dict[str, float]], period: int = 14) -> float:
    ranges = true_ranges(candles)

    if len(ranges) < period:
        raise ValueError(f"Need at least {period} candles for ATR")

    return sum(ranges[-period:]) / period