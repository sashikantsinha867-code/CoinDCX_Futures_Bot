import csv
import os
from datetime import datetime

ADS_LOG = "database/ads_log.csv"

HEADERS = [
    "Time",
    "Price",
    "EMA20",
    "EMA50",
    "RSI",
    "MACD",
    "MACD_SIGNAL",
    "ADX",
    "ATR",
    "Volume",
    "AvgVolume",
    "VolumeRatio",
    "Trend1H",
    "Signal",
    "Reason"
]


def log_ads(
    price,
    ema20,
    ema50,
    rsi,
    macd,
    macd_signal,
    adx,
    atr,
    volume,
    avg_volume,
    volume_ratio,
    trend,
    signal,
    reason
):

    os.makedirs("database", exist_ok=True)

    file_exists = os.path.exists(ADS_LOG)

    with open(ADS_LOG, "a", newline="") as f:

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(HEADERS)

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(price, 2),
            round(ema20, 2),
            round(ema50, 2),
            round(rsi, 2),
            round(macd, 2),
            round(macd_signal, 2),
            round(adx, 2),
            round(atr, 2),
            round(volume, 2),
            round(avg_volume, 2),
            round(volume_ratio, 2),
            trend,
            signal,
            reason
        ])

    print(f"📊 ADS Logged : {signal} | {reason}")