from typing import List, Dict


def ema(values: List[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"Need at least {period} values for EMA")
    multiplier = 2 / (period + 1)
    current_ema = sum(values[:period]) / period
    for price in values[period:]:
        current_ema = (price - current_ema) * multiplier + current_ema
    return current_ema


def ema_series(values: List[float], period: int) -> List[float]:
    if len(values) < period:
        raise ValueError(f"Need at least {period} values for EMA")
    multiplier = 2 / (period + 1)
    series = [sum(values[:period]) / period]
    for price in values[period:]:
        series.append((price - series[-1]) * multiplier + series[-1])
    return series


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
        previous_close = candle["close"] if i == 0 else candles[i - 1]["close"]
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
    current_atr = sum(ranges[:period]) / period
    for tr in ranges[period:]:
        current_atr = ((current_atr * (period - 1)) + tr) / period
    return current_atr


def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    if len(values) < slow + signal:
        raise ValueError(f"Need at least {slow + signal} values for MACD")
    fast_series = ema_series(values, fast)
    slow_series = ema_series(values, slow)
    offset = slow - fast
    macd_line = [fast_series[offset + i] - slow_series[i] for i in range(len(slow_series))]
    signal_series = ema_series(macd_line, signal)
    current_macd = macd_line[-1]
    current_signal = signal_series[-1]
    return {
        "macd": round(current_macd, 5),
        "signal": round(current_signal, 5),
        "histogram": round(current_macd - current_signal, 5),
    } 'histogram'