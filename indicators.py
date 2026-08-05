ema_50 = ema(closes, 50)
    ema_200 = ema(closes, 200)
    rsi_14 = rsi(closes, 14)
    atr_14 = atr(values, 14) # Pass the raw candle dicts for ATR
    macd_data = macd(closes) # Returns a dict with 'macd', 'signal', 'histogram'