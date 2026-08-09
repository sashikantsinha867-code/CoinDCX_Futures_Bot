import pandas as pd


def generate_signal(df):
    """
    ==================================================
    Strategy:
    1M SMA44 + Closed Candle Confirmation + Volume
    ==================================================

    IMPORTANT:
        The latest candle (-1) may still be forming.
        Therefore, signal is generated using the
        last CLOSED candle (-2).

    BUY:
        1. Previous closed candle interacts with SMA44
        2. Confirmation candle closes above SMA44
        3. Confirmation candle is bullish
        4. Volume > previous 20-candle average * 1.2
        5. SMA touch alone does NOT trigger entry

    SELL:
        1. Previous closed candle interacts with SMA44
        2. Confirmation candle closes below SMA44
        3. Confirmation candle is bearish
        4. Volume > previous 20-candle average * 1.2
        5. SMA touch alone does NOT trigger entry

    Otherwise:
        HOLD

    Stop Loss / Take Profit / Breakeven /
    Trailing SL are handled elsewhere.
    """

    # ==================================================
    # DATA VALIDATION
    # ==================================================

    if df is None or len(df) < 50:
        return "HOLD"

    required_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "SMA44",
    ]

    for column in required_columns:
        if column not in df.columns:
            return "HOLD"

    # Need at least:
    # - previous candle
    # - confirmation candle
    if len(df) < 46:
        return "HOLD"

    # ==================================================
    # CLOSED CANDLES
    # ==================================================

    # Latest candle (-1) may still be forming.
    # Use (-2) as the last CLOSED confirmation candle.

    confirmation = df.iloc[-2]
    previous = df.iloc[-3]

    # ==================================================
    # NAN CHECK
    # ==================================================

    required_values = [
        previous["open"],
        previous["high"],
        previous["low"],
        previous["close"],
        previous["SMA44"],
        previous["volume"],

        confirmation["open"],
        confirmation["high"],
        confirmation["low"],
        confirmation["close"],
        confirmation["SMA44"],
        confirmation["volume"],
    ]

    if any(pd.isna(value) for value in required_values):
        return "HOLD"

    # ==================================================
    # VOLUME CONFIRMATION
    # ==================================================

    # Average volume of candles BEFORE confirmation candle.
    # This avoids including the confirmation candle itself
    # in its own volume average.

    avg_volume = (
        df["volume"]
        .rolling(window=20)
        .mean()
        .shift(1)
        .iloc[-2]
    )

    if pd.isna(avg_volume) or avg_volume <= 0:
        return "HOLD"

    volume_ratio = confirmation["volume"] / avg_volume

    volume_confirmation = (
        confirmation["volume"] > avg_volume * 1.2
    )

    if not volume_confirmation:
        return "HOLD"

    # ==================================================
    # CANDLE CONFIRMATION
    # ==================================================

    bullish_candle = (
        confirmation["close"] > confirmation["open"]
    )

    bearish_candle = (
        confirmation["close"] < confirmation["open"]
    )

    # ==================================================
    # BUY SETUP
    # ==================================================

    # Previous candle interacted with SMA44.
    previous_touched_sma_buy = (
        previous["low"] <= previous["SMA44"]
    )

    # Confirmation candle closes ABOVE SMA44
    # and is bullish.

    bullish_reclaim = (
        bullish_candle
        and confirmation["close"] > confirmation["SMA44"]
    )

    if (
        previous_touched_sma_buy
        and bullish_reclaim
    ):
        print(
            "\n🟢 SMA44 BUY CONFIRMATION"
        )

        print(
            f"Previous Low : {previous['low']:.2f}"
        )

        print(
            f"Previous SMA44 : {previous['SMA44']:.2f}"
        )

        print(
            f"Confirmation Close : "
            f"{confirmation['close']:.2f}"
        )

        print(
            f"Confirmation SMA44 : "
            f"{confirmation['SMA44']:.2f}"
        )

        print(
            f"Volume Ratio : {volume_ratio:.2f}x"
        )

        return "BUY"

    # ==================================================
    # SELL SETUP
    # ==================================================

    # Previous candle interacted with SMA44.

    previous_touched_sma_sell = (
        previous["high"] >= previous["SMA44"]
    )

    # Confirmation candle closes BELOW SMA44
    # and is bearish.

    bearish_rejection = (
        bearish_candle
        and confirmation["close"] < confirmation["SMA44"]
    )

    if (
        previous_touched_sma_sell
        and bearish_rejection
    ):
        print(
            "\n🔴 SMA44 SELL CONFIRMATION"
        )

        print(
            f"Previous High : {previous['high']:.2f}"
        )

        print(
            f"Previous SMA44 : {previous['SMA44']:.2f}"
        )

        print(
            f"Confirmation Close : "
            f"{confirmation['close']:.2f}"
        )

        print(
            f"Confirmation SMA44 : "
            f"{confirmation['SMA44']:.2f}"
        )

        print(
            f"Volume Ratio : {volume_ratio:.2f}x"
        )

        return "SELL"

    # ==================================================
    # HOLD
    # ==================================================

    return "HOLD"

