import pandas as pd
from exchange.api import get_candles


def get_market_data():
    candles = get_candles()

    if candles is None:
        return None

    df = pd.DataFrame(candles)

    # Timestamp ko readable format me convert kare
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    # Oldest candle upar aur latest niche
    df = df.sort_values("time").reset_index(drop=True)

    return df