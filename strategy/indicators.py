import ta


def add_indicators(df):
    """
    BTC 15M strategy indicators.

    Active indicators:
        RSI(14)
        ATR(14)
        ADX(14)

    SMA44, EMA20, EMA50 and MACD are intentionally not used.
    """

    df = df.copy()

    # RSI(14)
    df["RSI"] = ta.momentum.rsi(
        close=df["close"],
        window=14
    )

    # ATR(14)
    atr = ta.volatility.AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["ATR"] = atr.average_true_range()

    # ADX(14)
    adx = ta.trend.ADXIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["ADX"] = adx.adx()

    # Remove incomplete indicator rows
    df = df.dropna().reset_index(drop=True)

    return df
