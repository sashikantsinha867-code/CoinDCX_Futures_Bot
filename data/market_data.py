import pandas as pd
from exchange.api import get_candles


def get_market_data(interval="15m", pair="B-BTC_USDT", limit=100):
    """
    Fetch market data.

    CoinDCX API supports:
        1m, 15m, 1h, 1d

    For 5m:
        Fetch 1m candles and aggregate locally into closed 5m candles.
    """

    if interval == "5m":
        candles = get_candles(
            pair=pair,
            interval="1m",
            limit=min(limit * 5 + 10, 1000)
        )
    else:
        candles = get_candles(
            pair=pair,
            interval=interval,
            limit=limit
        )

    if candles is None:
        return None

    df = pd.DataFrame(candles)

    if df.empty:
        return None

    df["time"] = pd.to_datetime(df["time"], unit="ms")

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("time").reset_index(drop=True)

    if interval == "5m":
        df = (
            df.set_index("time")
            .resample("5min")
            .agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            })
            .dropna()
            .reset_index()
        )

        # Use only completed 5-minute candles
        now_utc = pd.Timestamp.now(tz="UTC").tz_localize(None)
        current_bucket = now_utc.floor("5min")

        df = df[df["time"] < current_bucket]

        df = df.tail(limit).reset_index(drop=True)

    return df
