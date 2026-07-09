from data.market_data import get_market_data
from strategy.indicators import add_indicators
from strategy.signals import generate_signal
from strategy.risk import calculate_position_size
from paper_trade.paper_trade import paper_trade
from config import CAPITAL, RISK_PERCENT, TEST_MODE


def run_bot():

    print("=" * 50)
    print("CoinDCX Futures Trading Bot")
    print("=" * 50)

    # Market Data
    df = get_market_data()

    if df is None:
        print("❌ Failed to fetch market data.")
        return

    # Indicators
    df = add_indicators(df)

    last = df.iloc[-1]

    high = last["high"]
    low = last["low"]

    # Signal
    trade_signal = generate_signal(df)

    # TEST MODE
    if TEST_MODE:
        print("\n🧪 TEST MODE ENABLED")
        trade_signal = "BUY"

    # Risk
    entry = last["close"]
    sl = entry - (last["ATR"] * 1.5)
    tp = entry + ((entry - sl) * 2)

    qty = calculate_position_size(
        capital=CAPITAL,
        risk_percent=RISK_PERCENT,
        entry_price=entry,
        stop_loss_price=sl
    )

    # Output
    print("\n========== MARKET ==========")
    print(f"Price  : {entry:.2f}")
    print(f"EMA20  : {last['EMA20']:.2f}")
    print(f"EMA50  : {last['EMA50']:.2f}")
    print(f"RSI    : {last['RSI']:.2f}")
    print(f"MACD   : {last['MACD']:.2f}")
    print(f"ATR    : {last['ATR']:.2f}")

    print("\n========== SIGNAL ==========")
    print(f"Signal : {trade_signal}")

    print("\n========== RISK ==========")
    print(f"Entry  : {entry:.2f}")
    print(f"SL     : {sl:.2f}")
    print(f"TP     : {tp:.2f}")
    print(f"Qty    : {qty}")

    # Execute Paper Trade
    paper_trade(
        trade_signal,
        entry,
        high,
        low,
        qty,
        sl,
        tp
    )