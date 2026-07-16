from data.market_data import get_market_data
from strategy.indicators import add_indicators
from strategy.signals import generate_signal
from strategy.risk import calculate_position_size
from paper_trade.paper_trade import paper_trade, load_position
from config import CAPITAL, RISK_PERCENT, TEST_MODE


def run_bot():

    print("=" * 50)
    print("CoinDCX Futures Trading Bot")
    print("=" * 50)

    # ==========================
    # Fetch Market Data
    # ==========================
    df = get_market_data()

    if df is None or df.empty:
        print("❌ Failed to fetch market data.")
        return

    # ==========================
    # Indicators
    # ==========================
    df = add_indicators(df)

    last = df.iloc[-1]

    high = float(last["high"])
    low = float(last["low"])
    entry = float(last["close"])

    atr = float(last["ATR"])

    # ==========================
    # Market Information
    # ==========================
    print("\n========== MARKET ==========")
    print(f"Price  : {entry:.2f}")
    print(f"EMA20  : {last['EMA20']:.2f}")
    print(f"EMA50  : {last['EMA50']:.2f}")
    print(f"RSI    : {last['RSI']:.2f}")
    print(f"MACD   : {last['MACD']:.2f}")
    print(f"ATR    : {atr:.2f}")

    # ==========================
    # Existing Position
    # ==========================
    position = load_position()

    print("\n===== DEBUG =====")
    print("Loaded Position:", position)
    print("=================")

    if position:

        print("\n📌 Existing Position Found")

        paper_trade(
            "HOLD",
            entry,
            high,
            low,
            position["qty"],
            position["sl"],
            position["tp"]
        )

        return

    # ==========================
    # Generate Signal
    # ==========================
    trade_signal = generate_signal(df)

    if TEST_MODE:
        print("\n🧪 TEST MODE ENABLED")
        # Agar force BUY karna ho to next line uncomment karo
        # trade_signal = "BUY"

    if trade_signal == "HOLD":
        print("\n========== SIGNAL ==========")
        print("Signal : HOLD")
        return

    # ==========================
    # Stop Loss / Take Profit
    # ==========================
    if trade_signal == "BUY":

        sl = entry - (atr * 1.5)
        tp = entry + ((entry - sl) * 2)

    elif trade_signal == "SELL":

        sl = entry + (atr * 1.5)
        tp = entry - ((sl - entry) * 2)

    else:
        print("Unknown Signal")
        return

    # ==========================
    # Position Size
    # ==========================
    qty = calculate_position_size(
        capital=CAPITAL,
        risk_percent=RISK_PERCENT,
        entry_price=entry,
        stop_loss_price=sl
    )

    # ==========================
    # Print Signal
    # ==========================
    print("\n========== SIGNAL ==========")
    print(f"Signal : {trade_signal}")

    print("\n========== RISK ==========")
    print(f"Entry  : {entry:.2f}")
    print(f"SL     : {sl:.2f}")
    print(f"TP     : {tp:.2f}")
    print(f"Risk   : {abs(entry-sl):.2f}")
    print(f"Reward : {abs(tp-entry):.2f}")
    print(f"RR     : 1 : {abs(tp-entry)/abs(entry-sl):.2f}")
    print(f"Qty    : {qty:.6f}")

    # ==========================
    # Execute Paper Trade
    # ==========================
    paper_trade(
        trade_signal,
        entry,
        high,
        low,
        qty,
        sl,
        tp
    )

    print("\n[✓] Bot Cycle Completed")