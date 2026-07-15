import csv
import os
from datetime import datetime

LOG_FILE = "logs/trades.csv"


def log_trade(signal, entry, exit_price, quantity, pnl, balance):
    file_exists = os.path.exists(LOG_FILE)

    pnl_percent = (pnl / balance * 100) if balance > 0 else 0

    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists or os.path.getsize(LOG_FILE) == 0:
            writer.writerow([
                "Date",
                "Signal",
                "Entry",
                "Exit",
                "Quantity",
                "PnL",
                "PnL%",
                "Balance"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            signal,
            round(entry, 2),
            round(exit_price, 2),
            round(quantity, 6),
            round(pnl, 2),
            round(pnl_percent, 2),
            round(balance, 2)
        ])