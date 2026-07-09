import csv
import os
from datetime import datetime

LOG_FILE = "logs/trades.csv"


def log_trade(signal, entry, exit_price, quantity, pnl, balance):

    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        # Agar file nayi hai to header likho
        if not file_exists or os.path.getsize(LOG_FILE) == 0:
            writer.writerow([
                "Date",
                "Signal",
                "Entry",
                "Exit",
                "Quantity",
                "PnL",
                "Balance"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            signal,
            round(entry, 2),
            round(exit_price, 2),
            round(quantity, 6),
            round(pnl, 2),
            round(balance, 2)
        ])