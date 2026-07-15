import json
import os

from utils.logger import log_trade
from utils.telegram import send_telegram_message
from paper_trade.portfolio import update_portfolio, get_balance

STATE_FILE = "database/state.json"

def load_position():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_position(position):
    with open(STATE_FILE, "w") as f:
        json.dump(position, f, indent=4)

def calculate_pnl(side, entry_price, exit_price, qty):
    """Sahi PnL: + for profit, - for loss"""
    if side == "LONG":
        return (exit_price - entry_price) * qty
    else: # SHORT
        return (entry_price - exit_price) * qty    

def paper_trade(signal, entry_price, high, low, quantity, stop_loss, take_profit):
    global balance

    position = load_position()
    try:
        balance = get_balance()
    except:
        balance = 5000 # fallback

    entry_price, quantity, stop_loss, take_profit = map(float, [entry_price, quantity, stop_loss, take_profit])
    risk = abs(entry_price - stop_loss) # 1R

    # ==========================
    # HOLD signal aur koi position nahi hai
    # ==========================
    if signal == "HOLD" and position is None:
        return

    # ==========================
    # BUY ENTRY
    # ==========================
    if signal == "BUY" and position is None:
        position = {
            "side": "LONG", "entry": entry_price, "qty": quantity,
            "sl": stop_loss, "tp": take_profit,
            "highest_price": entry_price, "lowest_price": entry_price,
            "breakeven_done": False,
        }
        save_position(position)
        log_trade("BUY", entry_price, 0, quantity, 0, balance)
        print("\n✅ PAPER BUY EXECUTED")
        send_telegram_message(f"""🟢 <b>BUY EXECUTED</b>
💰 Entry : {entry_price:.2f}
📦 Qty : {quantity}
🛑 Stop Loss : {stop_loss:.2f}
🎯 Take Profit : {take_profit:.2f}""")
        return

    # ==========================
    # SHORT ENTRY
    # ==========================
    if signal == "SELL" and position is None:
        position = {
            "side": "SHORT", "entry": entry_price, "qty": quantity,
            "sl": stop_loss, "tp": take_profit,
            "highest_price": entry_price, "lowest_price": entry_price,
            "breakeven_done": False,
        }
        save_position(position)
        log_trade("SELL", entry_price, 0, quantity, 0, balance)
        print("\n🔴 PAPER SHORT EXECUTED")
        send_telegram_message(f"""🔴 <b>SHORT EXECUTED</b>
💰 Entry : {entry_price:.2f}
📦 Qty : {quantity}
🛑 Stop Loss : {stop_loss:.2f}
🎯 Take Profit : {take_profit:.2f}""")
        return

    # ==========================
    # POSITION MANAGEMENT
    # ==========================
    if position is not None:
        current_price = (high + low) / 2 # Current price estimate

        # Update trailing highs/lows
        if position["side"] == "LONG":
            position["highest_price"] = max(position["highest_price"], high)
            unrealized_pnl = (current_price - position["entry"]) * position["qty"]
        else:  # SHORT
            position["lowest_price"] = min(position["lowest_price"], low)
            unrealized_pnl = (position["entry"] - current_price) * position["qty"]

        # ==========================
        # BREAKEVEN + TRAILING STOP LOGIC
        # ==========================
        trail_triggered = False
        msg = ""
        
        if position["side"] == "LONG":
            profit = position["highest_price"] - position["entry"]
            
            if not position["breakeven_done"] and profit >= risk:
                position["sl"] = round(position["entry"] + 0.5, 2)
                position["breakeven_done"] = True
                trail_triggered = True
                msg = f"🔄 <b>BREAKEVEN HIT - LONG</b>\n\nSL moved to: {position['sl']:.2f}"

            elif position["breakeven_done"] and profit > 0:
                new_sl = position["entry"] + (profit * 0.50)
                if new_sl > position["sl"]:
                    old_sl = position["sl"]
                    position["sl"] = round(new_sl, 2)
                    trail_triggered = True
                    msg = f"🔄 <b>TRAILING SL UPDATED - LONG</b>\n\nOld SL : {old_sl:.2f}\nNew SL : {position['sl']:.2f}"

        else:  # SHORT
            profit = position["entry"] - position["lowest_price"]

            if not position["breakeven_done"] and profit >= risk:
                position["sl"] = round(position["entry"] - 0.5, 2)
                position["breakeven_done"] = True
                trail_triggered = True
                msg = f"🔄 <b>BREAKEVEN HIT - SHORT</b>\n\nSL moved to: {position['sl']:.2f}"

            elif position["breakeven_done"] and profit > 0:
                new_sl = position["entry"] - (profit * 0.50)
                if new_sl < position["sl"]:
                    old_sl = position["sl"]
                    position["sl"] = round(new_sl, 2)
                    trail_triggered = True
                    msg = f"🔄 <b>TRAILING SL UPDATED - SHORT</b>\n\nOld SL : {old_sl:.2f}\nNew SL : {position['sl']:.2f}"

        if trail_triggered:
            save_position(position)
            print(f"\n🔄 SL UPDATED : {position['sl']:.2f}")
            send_telegram_message(msg)

        save_position(position)

        print("\n📈 Position Still Open")
        print(f"Current Price : {current_price:.2f}")
        print(f"Current SL    : {position['sl']:.2f}")
        print(f"Current PnL   : {unrealized_pnl:.2f}")

        # ==========================
        # STOP LOSS
        # ==========================
        sl_hit = (position["side"] == "LONG" and low <= position["sl"]) or \
                 (position["side"] == "SHORT" and high >= position["sl"])

        if sl_hit:
            pnl = calculate_pnl(position["side"], position["entry"], position["sl"], position["qty"])
            pnl = -abs(pnl) # Safety: SL par hamesha loss
            trade_type = "SELL_SL" if position["side"] == "LONG" else "BUY_SL"

            portfolio = update_portfolio(pnl)
            balance = portfolio["balance"]
            log_trade(trade_type, position["entry"], position["sl"], position["qty"], pnl, balance)

            print("\n🛑 STOP LOSS HIT")
            send_telegram_message(f"""🛑 <b>STOP LOSS HIT</b>
💸 Loss : {pnl:.2f}
💼 Balance : {balance:.2f}""")

            position = None
            save_position(None)
            return

        # ==========================
        # TAKE PROFIT
        # ==========================
        tp_hit = (position["side"] == "LONG" and high >= position["tp"]) or \
                 (position["side"] == "SHORT" and low <= position["tp"])

        if tp_hit:
            pnl = calculate_pnl(position["side"], position["entry"], position["tp"], position["qty"])
            trade_type = "SELL_TP" if position["side"] == "LONG" else "BUY_TP"

            portfolio = update_portfolio(pnl)
            balance = portfolio["balance"]
            log_trade(trade_type, position["entry"], position["tp"], position["qty"], pnl, balance)

            print("\n🎯 TAKE PROFIT HIT")
            send_telegram_message(f"""🎯 <b>TAKE PROFIT HIT</b>
💰 Profit : {pnl:.2f}
💼 Balance : {balance:.2f}""")

            position = None
            save_position(None)
            return