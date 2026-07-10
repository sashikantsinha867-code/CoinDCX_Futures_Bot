def generate_signal(df):
    """
    Generate BUY / SELL / HOLD signal
    """

    if df is None or len(df) < 50:
        return "HOLD"

    last = df.iloc[-1]

    ema20 = last["EMA20"]
    ema50 = last["EMA50"]

    rsi = last["RSI"]

    macd = last["MACD"]
    macd_signal = last["MACD_SIGNAL"]

    # Indicator validation
    if (
        ema20 != ema20 or
        ema50 != ema50 or
        rsi != rsi or
        macd != macd or
        macd_signal != macd_signal
    ):
        return "HOLD"

    # LONG
    if (
        ema20 > ema50 and
        rsi > 55 and
        macd > macd_signal
    ):
        return "BUY"

    # SHORT
    if (
        ema20 < ema50 and
        rsi < 45 and
        macd < macd_signal
    ):
        return "SELL"

    return "HOLD"