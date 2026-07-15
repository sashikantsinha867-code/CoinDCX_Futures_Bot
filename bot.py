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

    # Fetch Market Data
    df = get_market_data()

    if df is None:
        print("❌ Failed to fetch market data.")
        return

    # Indicators
    df = add_indicators(df)

    last = df.iloc[-1]

    high = last["high"]
    low = last["low"]
    entry = last["close"]

    # Show Market
    print("\n========== MARKET ==========")
    print(f"Price  : {entry:.2f}")
    print(f"EMA20  : {last['EMA20']:.2f}")
    print(f"EMA50  : {last['EMA50']:.2f}")
    print(f"RSI    : {last['RSI']:.2f}")
    print(f"MACD   : {last['MACD']:.2f}")
    print(f"ATR    : {last['ATR']:.2f}")

    # Check Existing Position
    position = load_position()

    print("\n===== DEBUG =====")
    print("Loaded Position:", position)
    print("=================")

    if position is not None:
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

    # Generate Signal
    trade_signal = generate_signal(df)

    if TEST_MODE:
        print("\n🧪 TEST MODE ENABLED - Forcing BUY")
        trade_signal = "BUY"

    # Risk - RR 1:2 for BOTH LONG AND SHORT
    atr = last["ATR"]
    
    if trade_signal == "BUY":
        sl = entry - (atr * 1.5)
        tp = entry + ((entry - sl) * 2)  # TP upar
    elif trade_signal == "SELL":
        sl = entry + (atr * 1.5) 
        tp = entry - ((sl - entry) * 2)  # TP neeche
    else:
        print("No Signal")
        return

    qty = calculate_position_size(
        capital=CAPITAL,
        risk_percent=RISK_PERCENT,
        entry_price=entry,
        stop_loss_price=sl
    )

    print("\n========== SIGNAL ==========")
    print(f"Signal : {trade_signal}")

    print("\n========== RISK ==========")
    print(f"Entry  : {entry:.2f}")
    print(f"SL     : {sl:.2f}")
    print(f"TP     : {tp:.2f}")
    print(f"Risk   : {abs(entry-sl):.2f}")
    print(f"Reward : {abs(tp-entry):.2f}")
    print(f"Qty    : {qty:.6f}")

    paper_trade(
        trade_signal,
        entry,
        high,
        low,
        qty,
        sl,
        tp
    )