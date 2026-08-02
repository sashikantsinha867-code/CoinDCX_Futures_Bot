import pandas as pd


def generate_signal(df):
    """
    ==================================================
    Strategy:
    EMA20 + EMA50 + RSI + MACD + Volume + ADX
    ==================================================

    BUY:
        EMA20 > EMA50
        RSI > 55
        MACD > MACD_SIGNAL
        Volume > AVG_VOLUME * 1.2
        ADX > 25

    SELL:
        EMA20 < EMA50
        RSI < 45
        MACD < MACD_SIGNAL
        Volume > AVG_VOLUME * 1.2
        ADX > 25

    Otherwise:
        HOLD
    """

    # Data Validation
    if df is None or len(df) < 50:
        return "HOLD"

    last = df.iloc[-1]

    # Check NaN Values
    if last.isnull().any():
        return "HOLD"

    # Indicators
    ema20 = last["EMA20"]
    ema50 = last["EMA50"]

    rsi = last["RSI"]

    macd = last["MACD"]
    macd_signal = last["MACD_SIGNAL"]

    adx = last["ADX"]

    volume = last["volume"]
    avg_volume = last["AVG_VOLUME"]

    # ==========================
    # BUY SIGNAL
    # ==========================
    if (
        ema20 > ema50
        and rsi > 55
        and macd > macd_signal
        and volume > avg_volume * 1.2
        and adx > 25
    ):
        return "BUY"

    # ==========================
    # SELL SIGNAL
    # ==========================
    elif (
        ema20 < ema50
        and rsi < 45
        and macd < macd_signal
        and volume > avg_volume * 1.2
        and adx > 25
    ):
        return "SELL"

    # ==========================
    # HOLD
    # ==========================
    return "HOLD"