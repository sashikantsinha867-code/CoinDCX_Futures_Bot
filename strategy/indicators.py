import ta


def add_indicators(df):
    """
    Add technical indicators to DataFrame
    """

    # ==========================
    # EMA
    # ==========================
    df["EMA20"] = ta.trend.ema_indicator(
        close=df["close"],
        window=20
    )

    df["EMA50"] = ta.trend.ema_indicator(
        close=df["close"],
        window=50
    )

    # ==========================
    # RSI
    # ==========================
    df["RSI"] = ta.momentum.rsi(
        close=df["close"],
        window=14
    )

    # ==========================
    # MACD
    # ==========================
    macd = ta.trend.MACD(
        close=df["close"],
        window_slow=26,
        window_fast=12,
        window_sign=9
    )

    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()
    df["MACD_HIST"] = macd.macd_diff()

    # ==========================
    # ATR
    # ==========================
    atr = ta.volatility.AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["ATR"] = atr.average_true_range()

    # ==========================
    # ADX
    # ==========================
    adx = ta.trend.ADXIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["ADX"] = adx.adx()

    # ==========================
    # Volume Indicators
    # ==========================
    df["AVG_VOLUME"] = df["volume"].rolling(window=20).mean()

    # Volume Ratio
    df["VOLUME_RATIO"] = (
        df["volume"] / df["AVG_VOLUME"]
    )

    # ==========================
    # Remove NaN values
    # ==========================
    df = df.dropna().reset_index(drop=True)

    return df