def generate_signal(df):
    """
    Generate BUY / SELL / HOLD signal
    """

    last = df.iloc[-1]

    ema20 = last["EMA20"]
    ema50 = last["EMA50"]

    rsi = last["RSI"]

    macd = last["MACD"]
    signal = last["MACD_SIGNAL"]

    # BUY
    if (
        ema20 > ema50 and
        rsi > 55 and
        macd > signal
    ):
        return "BUY"

    # SELL
    elif (
        ema20 < ema50 and
        rsi < 45 and
        macd < signal
    ):
        return "SELL"

    # Otherwise
    return "HOLD"