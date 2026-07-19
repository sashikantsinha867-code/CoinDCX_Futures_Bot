import csv
import os
from datetime import datetime

LOG_FILE = "database/trades.csv"
FILE_HEADERS = ["Date", "Signal", "Entry", "Exit", "Quantity", "PnL", "PnL%", "Balance"]

def log_trade(signal, entry, exit_price, quantity, pnl, balance):
    os.makedirs("database", exist_ok=True)
    
    # PnL% sahi se nikalo. Entry pe hi calculate hoga
    pnl_percent = 0
    if entry > 0 and quantity > 0:
        pnl_percent = (pnl / (entry * quantity)) * 100

    # Agar Exit 0 hai to TP/SL nahi laga abhi
    exit_val = exit_price if exit_price > 0 else 0

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        signal,
        round(entry, 2),
        round(exit_val, 2),
        round(quantity, 6),
        round(pnl, 2),
        round(pnl_percent, 2),
        round(balance, 2)
    ]

    file_exists = os.path.exists(LOG_FILE)
    
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        # Header sirf 1 baar likho
        if not file_exists:
            writer.writerow(FILE_HEADERS)
        writer.writerow(row)
    
    print(f"📝 Logged: {signal} | PnL: {pnl:.2f} | Balance: {balance:.2f}")