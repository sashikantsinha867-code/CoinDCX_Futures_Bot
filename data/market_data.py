import pandas as pd
from exchange.api import get_candles


def get_market_data(interval="1m", pair="B-BTC_USDT", limit=100):
    """
    Fetch market data for any timeframe.

    Default:
        1 minute candles

    Examples:
        get_market_data()          -> 1m candles
        get_market_data("1m")      -> 1m candles
        get_market_data("15m")     -> 15m candles
        get_market_data("1h")      -> 1h candles
    """

    candles = get_candles(
        pair=pair,
        interval=interval,
        limit=limit
    )

    if candles is None:
        return None

    df = pd.DataFrame(candles)

    # Timestamp to readable format
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    # Oldest candle first
    df = df.sort_values("time").reset_index(drop=True)

    return df

