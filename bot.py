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
    print("=" * 50)

    # ==========================
    # 15 Minute Market Data
    # ==========================
    df = get_market_data("15m")

    if df is None or df.empty:
        print("❌ Failed to fetch 15m market data.")
        return

    df = add_indicators(df)

    # ==========================
    # 1 Hour Market Data
    # ==========================
    df_1h = get_market_data("1h")

    if df_1h is None or df_1h.empty:
        print("❌ Failed to fetch 1H market data.")
        return

    df_1h = add_indicators(df_1h)

    last_1h = df_1h.iloc[-1]

    trend_buy = last_1h["EMA20"] > last_1h["EMA50"]
    trend_sell = last_1h["EMA20"] < last_1h["EMA50"]

    print("\n========== HIGHER TIMEFRAME ==========")
    print(f"1H EMA20 : {last_1h['EMA20']:.2f}")
    print(f"1H EMA50 : {last_1h['EMA50']:.2f}")

    if trend_buy:
        trend = "BULLISH"
    elif trend_sell:
        trend = "BEARISH"
    else:
        trend = "SIDEWAYS"

    print(f"Trend    : {trend}")

    # ==========================
    # Indicators - 15m
    # ==========================
    last = df.iloc[-1]

    high = float(last["high"])
    low = float(last["low"])
    entry = float(last["close"])

    atr = float(last["ATR"])
    if atr <= 0:
        print("❌ Invalid ATR")
        return

    # ADS Logger Data
    ema20 = float(last["EMA20"])
    ema50 = float(last["EMA50"])
    rsi = float(last["RSI"])
    macd = float(last["MACD"])
    macd_signal = float(last["MACD_SIGNAL"])
    adx = float(last["ADX"])
    volume = float(last["volume"])
    avg_volume = float(last["AVG_VOLUME"])
    volume_ratio = float(last["VOLUME_RATIO"])    

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
    reason = "Strategy Signal"

    if TEST_MODE:
        print("\n🧪 TEST MODE ENABLED")
        # Agar force BUY karna ho to next line uncomment karo
        # trade_signal = "BUY"

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
            trend=trend,
            signal="HOLD",
            reason=reason
        )

        print("\n========== SIGNAL ==========")
        print("Signal : HOLD")
        return

    # ==========================
    # Multi-Timeframe Confirmation
    # ==========================
    if trade_signal == "BUY" and not trend_buy:
        print("❌ BUY rejected (1H trend is bearish)")
        trade_signal = "HOLD"
        reason = "BUY Rejected by 1H Trend"

    elif trade_signal == "SELL" and not trend_sell:
        print("❌ SELL rejected (1H trend is bullish)")
        trade_signal = "HOLD"
        reason = "SELL Rejected by 1H Trend"

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
            trend=trend,
            signal="HOLD",
            reason=reason
        )

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
        trend=trend,
        signal=trade_signal,
        reason=reason
    )

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