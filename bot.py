from data.market_data import get_market_data
from strategy.indicators import add_indicators
from strategy.signals import generate_signal
from strategy.risk import calculate_position_size
from paper_trade.paper_trade import paper_trade, load_position
from config import CAPITAL, RISK_PERCENT, TEST_MODE
from utils.ads_logger import log_ads


def run_bot():

    print("=" * 50)
    print("CoinDCX Futures Trading Bot")
    print("Strategy: 1M SMA44 + Candle Confirmation + Volume")
    print("=" * 50)

    # ==================================================
    # 1 MINUTE MARKET DATA
    # ==================================================

    df = get_market_data(
        interval="1m",
        pair="B-BTC_USDT",
        limit=200
    )

    if df is None or df.empty:
        print("❌ Failed to fetch 1m market data.")
        return

    # ==================================================
    # INDICATORS
    # ==================================================
    #
    # add_indicators() is still used because ATR,
    # volume information and existing logging/risk
    # calculations depend on it.
    #
    # SMA44 itself is calculated inside strategy.py.

    df = add_indicators(df)

    # ==================================================
    # LAST 1-MINUTE CANDLE
    # ==================================================

    last = df.iloc[-1]

    high = float(last["high"])
    low = float(last["low"])
    entry = float(last["close"])

    # ==================================================
    # ATR FOR EXISTING SL/TP
    # ==================================================

    if "ATR" not in df.columns:
        print("❌ ATR not available.")
        return

    atr = float(last["ATR"])

    if atr <= 0:
        print("❌ Invalid ATR")
        return

    # ==================================================
    # EXISTING INDICATOR DATA
    # ==================================================
    #
    # These are kept for ADS logger compatibility.
    # They are NOT used for generating the SMA44 signal.

    ema20 = float(last["EMA20"])
    ema50 = float(last["EMA50"])
    rsi = float(last["RSI"])
    macd = float(last["MACD"])
    macd_signal = float(last["MACD_SIGNAL"])
    adx = float(last["ADX"])
    volume = float(last["volume"])
    avg_volume = float(last["AVG_VOLUME"])
    volume_ratio = float(last["VOLUME_RATIO"])

    # ==================================================
    # MARKET INFORMATION
    # ==================================================

    print("\n========== 1M MARKET ==========")
    print(f"Price      : {entry:.2f}")
    print(f"SMA44      : {df['close'].rolling(44).mean().iloc[-1]:.2f}")
    print(f"Volume     : {volume:.2f}")
    print(f"Avg Volume : {avg_volume:.2f}")
    print(f"Vol Ratio  : {volume_ratio:.2f}")
    print(f"ATR        : {atr:.2f}")

    # ==================================================
    # EXISTING POSITION
    # ==================================================

    position = load_position()

    print("\n===== DEBUG =====")
    print("Loaded Position:", position)
    print("=================")

    if position:

        print("\n📌 Existing Position Found")

        # Existing SL / TP / Breakeven /
        # Trailing SL logic remains inside paper_trade()

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

    # ==================================================
    # GENERATE SMA44 SIGNAL
    # ==================================================

    trade_signal = generate_signal(df)

    reason = "SMA44 + Candle Confirmation + Volume"

    # ==================================================
    # TEST MODE
    # ==================================================

    if TEST_MODE:

        print("\n🧪 TEST MODE ENABLED")

        # Agar force BUY karna ho:
        # trade_signal = "BUY"

        # Agar force SELL karna ho:
        # trade_signal = "SELL"

    # ==================================================
    # HOLD
    # ==================================================

    if trade_signal == "HOLD":

        log_ads(
            price=entry,
            ema20=ema20,
            ema50=ema50,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            adx=adx,
            atr=atr,
            volume=volume,
            avg_volume=avg_volume,
            volume_ratio=volume_ratio,
            trend="SMA44",
            signal="HOLD",
            reason=reason
        )

        print("\n========== SIGNAL ==========")
        print("Signal : HOLD")

        return

    # ==================================================
    # SIGNAL CONFIRMED
    # ==================================================

    print("\n========== SIGNAL ==========")
    print(f"Signal : {trade_signal}")
    print("Confirmation : SMA44 + Candle + Volume")

    # ==================================================
    # STOP LOSS / TAKE PROFIT
    # ==================================================

    if trade_signal == "BUY":

        sl = entry - (atr * 1.5)

        tp = entry + ((entry - sl) * 2)

    elif trade_signal == "SELL":

        sl = entry + (atr * 1.5)

        tp = entry - ((sl - entry) * 2)

    else:

        print("Unknown Signal")
        return

    # ==================================================
    # POSITION SIZE
    # ==================================================

    qty = calculate_position_size(
        capital=CAPITAL,
        risk_percent=RISK_PERCENT,
        entry_price=entry,
        stop_loss_price=sl
    )

    # ==================================================
    # RISK INFORMATION
    # ==================================================

    risk_distance = abs(entry - sl)
    reward_distance = abs(tp - entry)

    print("\n========== RISK ==========")
    print(f"Entry  : {entry:.2f}")
    print(f"SL     : {sl:.2f}")
    print(f"TP     : {tp:.2f}")
    print(f"Risk   : {risk_distance:.2f}")
    print(f"Reward : {reward_distance:.2f}")

    if risk_distance > 0:
        print(
            f"RR     : 1 : "
            f"{reward_distance / risk_distance:.2f}"
        )

    print(f"Qty    : {qty:.6f}")

    # ==================================================
    # ADS LOGGER
    # ==================================================

    log_ads(
        price=entry,
        ema20=ema20,
        ema50=ema50,
        rsi=rsi,
        macd=macd,
        macd_signal=macd_signal,
        adx=adx,
        atr=atr,
        volume=volume,
        avg_volume=avg_volume,
        volume_ratio=volume_ratio,
        trend="SMA44",
        signal=trade_signal,
        reason=reason
    )

    # ==================================================
    # EXECUTE PAPER TRADE
    # ==================================================

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


if __name__ == "__main__":
    run_bot()
