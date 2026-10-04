import pandas as pd


# ==========================================================
# BTC 15M S/R + RSI + ADX + ATR STRATEGY
# ==========================================================

RSI_LONG_MAX = 40.0
RSI_SHORT_MIN = 60.0

ADX_MIN = 20.0

# Price must come reasonably close to S/R.
# 0.35% is used for BTC 15M.
SR_TOLERANCE = 0.0035

# ATR must be at least this percentage of price.
# Prevents extremely low-volatility/choppy conditions.
MIN_ATR_PERCENT = 0.0015


def _find_support_resistance(df):
    """
    Detect recent support and resistance from previous swing points.

    Only candles BEFORE the confirmation candle are used.
    """

    lookback = min(50, len(df) - 2)

    data = df.iloc[-(lookback + 2):-2].copy()

    if len(data) < 10:
        return None, None

    # Recent swing lows
    swing_lows = []
    swing_highs = []

    for i in range(2, len(data) - 2):

        low = float(data.iloc[i]["low"])
        high = float(data.iloc[i]["high"])

        prev_low_1 = float(data.iloc[i - 1]["low"])
        prev_low_2 = float(data.iloc[i - 2]["low"])
        next_low_1 = float(data.iloc[i + 1]["low"])
        next_low_2 = float(data.iloc[i + 2]["low"])

        prev_high_1 = float(data.iloc[i - 1]["high"])
        prev_high_2 = float(data.iloc[i - 2]["high"])
        next_high_1 = float(data.iloc[i + 1]["high"])
        next_high_2 = float(data.iloc[i + 2]["high"])

        if (
            low <= prev_low_1
            and low <= prev_low_2
            and low <= next_low_1
            and low <= next_low_2
        ):
            swing_lows.append(low)

        if (
            high >= prev_high_1
            and high >= prev_high_2
            and high >= next_high_1
            and high >= next_high_2
        ):
            swing_highs.append(high)

    if not swing_lows or not swing_highs:
        return None, None

    current_price = float(df.iloc[-2]["close"])

    # Nearest support below current price
    supports = [x for x in swing_lows if x <= current_price]

    # Nearest resistance above current price
    resistances = [x for x in swing_highs if x >= current_price]

    support = max(supports) if supports else None
    resistance = min(resistances) if resistances else None

    return support, resistance


def generate_signal(df: pd.DataFrame) -> str:
    """
    FINAL BTC 15M STRATEGY

    LONG:
        Support retest
        RSI(14) < 40
        ADX(14) >= 20
        ATR sufficient
        Bullish rejection candle
        RSI not in neutral zone

    SHORT:
        Resistance retest
        RSI(14) > 60
        ADX(14) >= 20
        ATR sufficient
        Bearish rejection candle
        RSI not in neutral zone

    SIDEWAYS:
        ADX < 20 -> NO TRADE
        RSI 45-55 -> NO TRADE
        Low ATR -> NO TRADE

    Returns:
        BUY
        SELL
        NONE
    """

    if df is None or len(df) < 60:
        return "NONE"

    df = df.copy()

    required = [
        "open",
        "high",
        "low",
        "close",
        "RSI",
        "ATR",
        "ADX",
    ]

    for column in required:
        if column not in df.columns:
            return "NONE"

    # ------------------------------------------------------
    # Use only CLOSED candles
    #
    # confirmation = latest closed candle
    # setup         = candle immediately before it
    # ------------------------------------------------------

    setup = df.iloc[-2]
    confirmation = df.iloc[-1]

    close_price = float(confirmation["close"])

    rsi = float(setup["RSI"])
    adx = float(setup["ADX"])
    atr = float(setup["ATR"])

    setup_open = float(setup["open"])
    setup_high = float(setup["high"])
    setup_low = float(setup["low"])
    setup_close = float(setup["close"])

    confirmation_open = float(confirmation["open"])
    confirmation_high = float(confirmation["high"])
    confirmation_low = float(confirmation["low"])
    confirmation_close = float(confirmation["close"])

    # ------------------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------------------

    if close_price <= 0 or atr <= 0:
        return "NONE"

    # ------------------------------------------------------
    # SIDEWAYS FILTER
    # ------------------------------------------------------

    if adx < ADX_MIN:
        return "NONE"

    atr_percent = atr / close_price

    if atr_percent < MIN_ATR_PERCENT:
        return "NONE"

    # Explicit neutral RSI filter
    if 45.0 <= rsi <= 55.0:
        return "NONE"

    # ------------------------------------------------------
    # SUPPORT / RESISTANCE
    # ------------------------------------------------------

    support, resistance = _find_support_resistance(df)

    if support is None and resistance is None:
        return "NONE"

    # ------------------------------------------------------
    # BULLISH REJECTION / SUPPORT BOUNCE
    # ------------------------------------------------------

    bullish_setup = setup_close > setup_open
    bullish_confirmation = confirmation_close > confirmation_open

    support_touch = False

    if support is not None:
        support_distance = abs(setup_low - support) / setup_close

        support_touch = (
            setup_low <= support * (1.0 + SR_TOLERANCE)
            and support_distance <= SR_TOLERANCE
        )

    # Confirmation must hold above setup high.
    bullish_break = confirmation_close > setup_high

    if (
        support_touch
        and rsi < RSI_LONG_MAX
        and bullish_setup
        and bullish_confirmation
        and bullish_break
    ):
        return "BUY"

    # ------------------------------------------------------
    # BEARISH REJECTION / RESISTANCE REJECTION
    # ------------------------------------------------------

    bearish_setup = setup_close < setup_open
    bearish_confirmation = confirmation_close < confirmation_open

    resistance_touch = False

    if resistance is not None:
        resistance_distance = abs(setup_high - resistance) / setup_close

        resistance_touch = (
            setup_high >= resistance * (1.0 - SR_TOLERANCE)
            and resistance_distance <= SR_TOLERANCE
        )

    # Confirmation must break below setup low.
    bearish_break = confirmation_close < setup_low

    if (
        resistance_touch
        and rsi > RSI_SHORT_MIN
        and bearish_setup
        and bearish_confirmation
        and bearish_break
    ):
        return "SELL"

    return "NONE"
