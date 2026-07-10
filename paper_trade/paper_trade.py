import json
import os

from utils.logger import log_trade
from utils.telegram import send_telegram_message
from paper_trade.portfolio import update_portfolio

STATE_FILE = "database/state.json"


def load_position():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_position(position):
    with open(STATE_FILE, "w") as f:
        json.dump(position, f, indent=4)


balance = 5000
position = load_position()


def paper_trade(signal, entry_price, high, low, quantity, stop_loss, take_profit):
    global position
    global balance

    # ==========================
    # BUY
    # ==========================
    if signal == "BUY" and position is None:

        position = {
            "side": "LONG",
            "entry": float(entry_price),
            "qty": float(quantity),
            "sl": float(stop_loss),
            "tp": float(take_profit)
        }

        save_position(position)

        log_trade(
            "BUY",
            entry_price,
            0,
            quantity,
            0,
            balance
        )

        print("\n✅ PAPER BUY EXECUTED")
        print(position)

        send_telegram_message(
            f"""
🟢 <b>BUY EXECUTED</b>

💰 Entry : {entry_price:.2f}
📦 Qty : {quantity}
🛑 Stop Loss : {stop_loss:.2f}
🎯 Take Profit : {take_profit:.2f}
"""
        )

        return

    # ==========================
    # POSITION OPEN
    # ==========================
    if position is not None:

        unrealized_pnl = (entry_price - position["entry"]) * position["qty"]

        print("\n📈 Position Still Open")
        print(position)

        print(f"\nCurrent Price : {entry_price:.2f}")
        print(f"Current PnL   : {unrealized_pnl:.2f}")

        # ==========================
        # STOP LOSS
        # ==========================
        if low <= position["sl"]:

            pnl = (position["sl"] - position["entry"]) * position["qty"]

            portfolio = update_portfolio(pnl)
            balance = portfolio["balance"]

            log_trade(
                "SELL_SL",
                position["entry"],
                position["sl"],
                position["qty"],
                pnl,
                balance
            )

            print("\n🛑 STOP LOSS HIT")
            print(f"PnL : {pnl:.2f}")
            print(f"Balance : {balance:.2f}")

            send_telegram_message(
                f"""
🔴 <b>STOP LOSS HIT</b>

💸 Loss : {pnl:.2f}

💼 Balance : {balance:.2f}
"""
            )

            position = None
            save_position(None)

            return

        # ==========================
        # TAKE PROFIT
        # ==========================
        if high >= position["tp"]:

            pnl = (position["tp"] - position["entry"]) * position["qty"]

            portfolio = update_portfolio(pnl)
            balance = portfolio["balance"]

            log_trade(
                "SELL_TP",
                position["entry"],
                position["tp"],
                position["qty"],
                pnl,
                balance
            )

            print("\n🎯 TAKE PROFIT HIT")
            print(f"PnL : {pnl:.2f}")
            print(f"Balance : {balance:.2f}")

            send_telegram_message(
                f"""
🟢 <b>TAKE PROFIT HIT</b>

💰 Profit : {pnl:.2f}

💼 Balance : {balance:.2f}
"""
            )

            position = None
            save_position(None)

            return