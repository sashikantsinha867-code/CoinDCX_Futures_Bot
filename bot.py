import os
import time
import json
from decimal import Decimal, ROUND_DOWN, ROUND_UP

from data.market_data import get_market_data
from strategy.signals import generate_signal
from strategy.risk import calculate_position_size

from exchange.orders import (
    place_futures_market_order,
    get_futures_positions,
    get_futures_orders,
    get_futures_available_balance,
    get_usdt_inr_conversion_rate,
    get_futures_instrument_details,
    create_futures_tpsl,
)

from config import (
    TEST_MODE,
    LEVERAGE,
    FUTURES_MARGIN,
)


FUTURES_PAIR = "B-BTC_USDT"
PRICE_TICK = Decimal("0.1")

# ==========================================================
# PRICE ROUNDING
# ==========================================================

def round_price(price, direction="down"):

    value = Decimal(str(price)) / PRICE_TICK

    rounding_mode = (
        ROUND_UP
        if direction == "up"
        else ROUND_DOWN
    )

    rounded = value.quantize(
        Decimal("1"),
        rounding=rounding_mode
    )

    return float(rounded * PRICE_TICK)


# ==========================================================
# MARKET DATA
# ==========================================================

def get_15m_data():

    df = get_market_data(
        interval="15m",
        pair=FUTURES_PAIR,
        limit=200
    )

    if df is None or df.empty:
        print("❌ Failed to fetch 15M market data.")
        return None

    required = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for col in required:

        if col not in df.columns:

            print(
                f"❌ Required 15M column missing: {col}"
            )

            return None

    return df


# ==========================================================
# POSITION HELPERS
# ==========================================================

def find_btc_position(positions):
    """
    Return only an active BTC Futures position.
    """

    if not positions:
        return None

    for position in positions:

        if position.get("pair") != FUTURES_PAIR:
            continue

        active_pos = float(
            position.get("active_pos", 0) or 0
        )

        if active_pos != 0:
            return position

    return None


def manage_existing_position(position, df):
    """
    Existing BTC Futures position protection.

    Uses the latest closed setup candle:
    LONG  -> SL = setup candle low
    SHORT -> SL = setup candle high
    TP    -> 1:3 Risk/Reward

    Existing TP/SL are not replaced if already active.
    """

    position_id = position.get("id")

    active_pos = float(
        position.get("active_pos", 0) or 0
    )

    entry_price = float(
        position.get("avg_price")
        or position.get("average_price")
        or 0
    )

    if not position_id or active_pos == 0 or entry_price <= 0:
        print("❌ Invalid active position.")
        return

    if df is None or len(df) < 3:
        print("❌ Not enough 15M candle data for SL/TP.")
        return

    # Same setup candle used by the strategy
    setup_candle = df.iloc[-2]

    setup_low = float(setup_candle["low"])
    setup_high = float(setup_candle["high"])

    # ------------------------------------------------------
    # POSITION SIDE
    # ------------------------------------------------------

    if active_pos > 0:
        side = "LONG"

        final_stop_loss = setup_low

        risk = entry_price - final_stop_loss

        if risk <= 0:
            print("❌ Invalid LONG SL.")
            print(f"Entry : {entry_price:.2f}")
            print(f"SL    : {final_stop_loss:.2f}")
            return

        final_take_profit = entry_price + (risk * 3)

    else:
        side = "SHORT"

        final_stop_loss = setup_high

        risk = final_stop_loss - entry_price

        if risk <= 0:
            print("❌ Invalid SHORT SL.")
            print(f"Entry : {entry_price:.2f}")
            print(f"SL    : {final_stop_loss:.2f}")
            return

        final_take_profit = entry_price - (risk * 3)

    # ------------------------------------------------------
    # ROUND TO BTC PRICE TICK
    # ------------------------------------------------------

    if side == "LONG":
        final_stop_loss = round_price(
            final_stop_loss,
            "down"
        )
        final_take_profit = round_price(
            final_take_profit,
            "up"
        )
    else:
        final_stop_loss = round_price(
            final_stop_loss,
            "up"
        )
        final_take_profit = round_price(
            final_take_profit,
            "down"
        )

    risk = abs(entry_price - final_stop_loss)
    reward = abs(final_take_profit - entry_price)

    actual_rr = (
        reward / risk
        if risk > 0
        else 0
    )

    print("\n========== EXISTING POSITION ==========")
    print("Position ID :", position_id)
    print("Position    :", side)
    print("Quantity    :", abs(active_pos))
    print(f"Entry       : {entry_price:.2f}")
    print(f"Setup Low   : {setup_low:.2f}")
    print(f"Setup High  : {setup_high:.2f}")
    print(f"SL          : {final_stop_loss:.2f}")
    print(f"TP          : {final_take_profit:.2f}")
    print(f"Risk        : {risk:.2f}")
    print(f"Reward      : {reward:.2f}")
    print(f"Risk/Reward : 1:{actual_rr:.2f}")

    existing_tp = float(
        position.get("take_profit_trigger", 0) or 0
    )

    existing_sl = float(
        position.get("stop_loss_trigger", 0) or 0
    )

    if existing_tp > 0:
        print(
            f"✅ Existing TP already active: "
            f"{existing_tp:.2f}"
        )
    else:
        print("⚠️ TP missing.")

    if existing_sl > 0:
        print(
            f"✅ Existing SL already active: "
            f"{existing_sl:.2f}"
        )
    else:
        print("⚠️ SL missing.")

    # ------------------------------------------------------
    # BOTH ALREADY ACTIVE
    # ------------------------------------------------------

    if existing_tp > 0 and existing_sl > 0:
        print("✅ TP + SL already active.")
        print("No new protection order required.")
        return

    # ------------------------------------------------------
    # CREATE TP + SL
    # ------------------------------------------------------

    print("\n🛡️ Creating TP + SL protection...")

    tpsl_status, tpsl_response = create_futures_tpsl(
        position_id=position_id,
        take_profit=final_take_profit,
        stop_loss=final_stop_loss,
        position_side=side
    )

    print("\n========== TP + SL RESPONSE ==========")
    print("STATUS   :", tpsl_status)
    print("RESPONSE :", tpsl_response)

    if tpsl_status in (200, 201):
        print("✅ TP + SL protection accepted.")
    else:
        print("❌ TP + SL placement FAILED.")
        print("⚠️ Position may remain unprotected.")


# ==========================================================
# MAIN
# ==========================================================

def run_bot():

    print("\n" + "=" * 60)
    print("CoinDCX Futures Trading Bot")
    print("Strategy: 15M S/R + RSI + ADX + 1:3 RR")
    print("Trailing: OFF")
    print("TP/SL: 1:3 RR")
    print("MODE: LIVE")
    print("=" * 60)

    # ======================================================
    # MARKET DATA
    # ======================================================

    df = get_15m_data()

    if df is None:
        return

    # ======================================================
    # POSITION CHECK FIRST
    # ======================================================

    status, positions = get_futures_positions()

    print("\n===== LIVE POSITION CHECK =====")
    print("STATUS:", status)
    print("POSITIONS:", positions)

    if status != 200:

        print(
            "❌ Could not fetch Futures positions."
        )

        return

    position = find_btc_position(positions)

    # ======================================================
    # EXISTING POSITION
    # ======================================================

    if position:

        print(
            "\n📌 Existing LIVE BTC Futures position found."
        )

        manage_existing_position(
            position,
            df
        )

        return

    # ======================================================
    # NO POSITION
    # ======================================================

    print(
        "\nNo existing BTC Futures position."
    )


    # ======================================================
    # CLOSED CANDLE
    # ======================================================

    # Last candle may still be forming.
    # Signal function receives only completed candles.
    if len(df) < 3:

        print(
            "❌ Not enough 15M candles."
        )

        return

    closed_df = df.iloc[:-1].copy()

    confirmation = closed_df.iloc[-1]
    previous = closed_df.iloc[-2]

    entry = float(
        confirmation["close"]
    )

    print("\n========== 15M MARKET ==========")
    print(
        f"Previous High  : {previous['high']:.2f}"
    )
    print(
        f"Previous Low   : {previous['low']:.2f}"
    )
    print(
        f"Previous Volume: {previous['volume']:.2f}"
    )

    print(
        f"Confirm Open   : {confirmation['open']:.2f}"
    )
    print(
        f"Confirm High   : {confirmation['high']:.2f}"
    )
    print(
        f"Confirm Low    : {confirmation['low']:.2f}"
    )
    print(
        f"Confirm Close  : {confirmation['close']:.2f}"
    )
    print(
        f"Confirm Volume : {confirmation['volume']:.2f}"
    )

    # ======================================================
    # SIGNAL
    # ======================================================

    trade_signal = generate_signal(
        closed_df
    )

    print("\n========== SIGNAL ==========")
    print("Signal :", trade_signal)

    if TEST_MODE:

        print(
            "\n❌ TEST_MODE is enabled."
        )

        print(
            "Live order blocked."
        )

        return

    if trade_signal not in (
        "BUY",
        "SELL"
    ):

        print(
            "LIVE ORDER : NONE"
        )

        return

    # ======================================================
    # NEW LIVE MARKET ORDER
    # 15M S/R + RSI + ADX — 1:3 TP + SL
    # ======================================================

    print("\n========== NEW LIVE ORDER ==========")
    print("Signal :", trade_signal)

    # ------------------------------------------------------
    # GET FUTURES BALANCE
    # ------------------------------------------------------

    balance_status, available_balance, balance_data = (
        get_futures_available_balance()
    )

    print("\n========== FUTURES BALANCE ==========")
    print("STATUS :", balance_status)
    print(f"AVAILABLE {FUTURES_MARGIN} :", available_balance)

    if balance_status != 200:
        print("❌ Futures balance API failed.")
        print("RESPONSE :", balance_data)
        return

    if available_balance <= 0:
        print("❌ No available Futures balance.")
        return

    # ------------------------------------------------------
    # GET INR -> USDT CONVERSION
    # ------------------------------------------------------

    conversion_status, usdt_inr_rate, conversion_data = (
        get_usdt_inr_conversion_rate()
    )

    print("\n========== USDT / INR CONVERSION ==========")
    print("STATUS :", conversion_status)
    print("RATE   :", usdt_inr_rate)

    if conversion_status != 200 or usdt_inr_rate <= 0:
        print("❌ Could not get USDT/INR conversion rate.")
        print("RESPONSE :", conversion_data)
        return

    # ------------------------------------------------------
    # CONVERT INR MARGIN TO USDT MARGIN
    # ------------------------------------------------------

    if FUTURES_MARGIN == "INR":
        available_usdt = (
            available_balance / usdt_inr_rate
        )
    else:
        available_usdt = available_balance

    print("\n========== MARGIN ==========")
    print(f"Available {FUTURES_MARGIN} :", available_balance)
    print("USDT/INR Rate       :", usdt_inr_rate)
    print("Available USDT      :", available_usdt)

    if available_usdt <= 0:
        print("❌ Available USDT margin is zero.")
        return

    # ------------------------------------------------------
    # LEVERAGE
    # ------------------------------------------------------

    leverage = int(LEVERAGE)

    if leverage <= 0:
        print("❌ Invalid leverage.")
        return

    # ======================================================
    # POSITION SIZING
    # Use 100% of available Futures margin.
    # Notional = margin × leverage.
    # ======================================================

    MARGIN_USAGE_PERCENT = 100.0

    trade_margin_usdt = (
        available_usdt
        * MARGIN_USAGE_PERCENT
        / 100.0
    )

    notional_usdt = (
        trade_margin_usdt
        * leverage
    )

    raw_quantity = (
        notional_usdt / entry
    )

    # ------------------------------------------------------
    # LIVE INSTRUMENT RULES
    # ------------------------------------------------------

    instrument_status, instrument = (
        get_futures_instrument_details()
    )

    print("\n========== INSTRUMENT ==========")
    print("STATUS :", instrument_status)

    if instrument_status != 200:
        print("❌ Instrument API failed.")
        print("RESPONSE :", instrument)
        return

    if not isinstance(instrument, dict):
        print("❌ Invalid instrument response.")
        print("RESPONSE :", instrument)
        return

    quantity_increment = float(
        instrument.get(
            "quantity_increment",
            0.001
        ) or 0.001
    )

    min_quantity = float(
        instrument.get(
            "min_quantity",
            0.001
        ) or 0.001
    )

    min_notional = float(
        instrument.get(
            "min_notional",
            0
        ) or 0
    )

    max_market_quantity = float(
        instrument.get(
            "max_market_order_quantity",
            9500
        ) or 9500
    )

    print(
        "Quantity Increment        :",
        quantity_increment
    )
    print(
        "Minimum Quantity          :",
        min_quantity
    )
    print(
        "Minimum Notional          :",
        min_notional
    )
    print(
        "Max Market Quantity      :",
        max_market_quantity
    )

    # ------------------------------------------------------
    # ROUND DOWN TO COINDCX QUANTITY STEP
    # ------------------------------------------------------

    from decimal import Decimal, ROUND_DOWN

    step = Decimal(
        str(quantity_increment)
    )

    quantity_decimal = (
        Decimal(str(raw_quantity)) / step
    ).to_integral_value(
        rounding=ROUND_DOWN
    ) * step

    quantity = float(
        quantity_decimal
    )

    print("\n========== POSITION SIZE ==========")
    print("Available Margin  :", available_usdt)
    print("Margin Usage %    :", MARGIN_USAGE_PERCENT)
    print("Trade Margin USDT :", trade_margin_usdt)
    print("Leverage          :", leverage)
    print("Entry Price       :", entry)
    print("Notional USDT     :", notional_usdt)
    print("Raw Quantity      :", raw_quantity)
    print("Final Quantity    :", quantity)

    # ------------------------------------------------------
    # SAFETY VALIDATION
    # ------------------------------------------------------

    if quantity < min_quantity:
        print(
            f"❌ Quantity {quantity} < minimum {min_quantity}"
        )
        return

    if quantity > max_market_quantity:
        print(
            f"❌ Quantity {quantity} > max market "
            f"quantity {max_market_quantity}"
        )
        return

    order_notional = (
        quantity * entry
    )

    if min_notional > 0 and order_notional < min_notional:
        print(
            f"❌ Order notional {order_notional:.4f} "
            f"is below minimum {min_notional}"
        )
        return

    # ------------------------------------------------------
    # PLACE MARKET ORDER
    # ------------------------------------------------------

    order_side = (
        "buy"
        if trade_signal == "BUY"
        else "sell"
    )

    print("\n========== PLACING MARKET ORDER ==========")
    print("Side              :", order_side.upper())
    print("Pair              :", FUTURES_PAIR)
    print("Quantity          :", quantity)
    print("Leverage          :", leverage)
    print("Margin Currency   :", FUTURES_MARGIN)

    order_status, order_response = (
        place_futures_market_order(
            side=order_side,
            pair=FUTURES_PAIR,
            quantity=quantity,
            leverage=leverage
        )
    )

    print("\n========== MARKET ORDER RESPONSE ==========")
    print("STATUS   :", order_status)
    print("RESPONSE :", order_response)

    if order_status not in (200, 201):
        print("❌ MARKET ORDER FAILED.")
        return

    print("✅ MARKET ORDER ACCEPTED.")

    # ------------------------------------------------------
    # WAIT FOR MARKET ORDER TO ACTUALLY FILL
    # ------------------------------------------------------

    order_id = None

    if isinstance(order_response, list) and order_response:
        order_id = order_response[0].get("id")

    elif isinstance(order_response, dict):
        order_id = order_response.get("id")

    print("\n========== WAITING FOR MARKET ORDER FILL ==========")
    print("Order ID :", order_id)

    if not order_id:
        print("❌ Market order ID missing.")
        print("⚠️ Cannot safely confirm fill.")
        return

    filled_order = None

    for attempt in range(10):

        time.sleep(1)

        orders_status, futures_orders = get_futures_orders(
            status="open,filled,partially_filled,cancelled,rejected",
            pair=FUTURES_PAIR,
            size="20"
        )

        print(f"\n🔎 Fill Check {attempt + 1}/10")
        print("STATUS :", orders_status)

        if orders_status != 200:
            print("⚠️ Could not fetch Futures orders.")
            continue

        if isinstance(futures_orders, list):
            order_list = futures_orders

        elif isinstance(futures_orders, dict):
            order_list = futures_orders.get(
                "data",
                futures_orders.get("orders", [])
            )

        else:
            order_list = []

        for order in order_list:

            if str(order.get("id")) != str(order_id):
                continue

            current_status = str(
                order.get("status", "")
            ).lower()

            remaining_quantity = float(
                order.get(
                    "remaining_quantity",
                    0
                ) or 0
            )

            avg_price = float(
                order.get(
                    "avg_price",
                    0
                ) or 0
            )

            print(
                "Order Status       :",
                current_status
            )
            print(
                "Remaining Quantity :",
                remaining_quantity
            )
            print(
                "Average Price      :",
                avg_price
            )

            if (
                current_status == "filled"
                and remaining_quantity == 0
                and avg_price > 0
            ):
                filled_order = order

                print(
                    "\n✅ MARKET ORDER FULLY FILLED."
                )
                break

            if current_status in (
                "cancelled",
                "rejected",
                "partially_cancelled"
            ):
                print(
                    f"❌ MARKET ORDER TERMINATED: "
                    f"{current_status}"
                )
                return

        if filled_order:
            break

    if not filled_order:
        print(
            "\n❌ MARKET ORDER NOT CONFIRMED FILLED."
        )
        print(
            "⚠️ TP NOT PLACED — SAFETY STOP."
        )
        return

    # ------------------------------------------------------
    # FETCH ACTUAL FILLED POSITION
    # ------------------------------------------------------

    print(
        "\n========== FETCHING FILLED POSITION =========="
    )

    position_status, positions_after_order = (
        get_futures_positions()
    )

    print(
        "STATUS    :",
        position_status
    )

    print(
        "POSITIONS :",
        positions_after_order
    )

    if position_status != 200:
        print(
            "❌ Could not fetch position after fill."
        )
        print(
            "⚠️ TP NOT PLACED."
        )
        return

    new_position = find_btc_position(
        positions_after_order
    )

    # Position API can lag slightly behind
    # the order fill, so retry once.
    if not new_position:

        print(
            "⚠️ Position not visible yet. Retrying..."
        )

        time.sleep(1)

        position_status, positions_after_order = (
            get_futures_positions()
        )

        print(
            "RETRY STATUS    :",
            position_status
        )

        print(
            "RETRY POSITIONS :",
            positions_after_order
        )

        new_position = find_btc_position(
            positions_after_order
        )

    if not new_position:
        print(
            "❌ BTC position still not found."
        )
        print(
            "⚠️ TP NOT PLACED."
        )
        return

    position_id = new_position.get("id")

    active_pos = float(
        new_position.get(
            "active_pos",
            0
        ) or 0
    )

    actual_entry = float(
        new_position.get(
            "avg_price"
        )
        or new_position.get(
            "average_price"
        )
        or 0
    )

    print("\n========== FILLED POSITION ==========")
    print("Position ID :", position_id)
    print("Active Pos  :", active_pos)
    print("Avg Price   :", actual_entry)

    if not position_id:
        print("❌ Position ID missing.")
        print("⚠️ TP NOT PLACED.")
        return

    if active_pos == 0:
        print("❌ Position quantity is zero.")
        print("⚠️ TP NOT PLACED.")
        return

    if actual_entry <= 0:
        print("❌ Invalid actual entry price.")
        print("⚠️ TP NOT PLACED.")
        return

    # ------------------------------------------------------
    # DETERMINE ACTUAL POSITION SIDE
    # ------------------------------------------------------

    # IMPORTANT:
    # Strategy uses:
    #   setup candle      = df.iloc[-2]
    #   confirmation      = df.iloc[-1]
    #
    # SL is based on the SAME setup candle.

    if closed_df is None or len(closed_df) < 3:
        print("❌ Not enough 15M candle data for SL/TP.")
        return

    setup_candle = closed_df.iloc[-2]

    setup_low = float(
        setup_candle["low"]
    )

    setup_high = float(
        setup_candle["high"]
    )

    if active_pos > 0:

        position_side = "LONG"

        # LONG:
        # SL = setup candle LOW
        final_stop_loss = setup_low

        risk = (
            actual_entry
            - final_stop_loss
        )

        if risk <= 0:
            print("❌ Invalid LONG setup-candle SL.")
            print(
                f"Entry : {actual_entry:.2f}"
            )
            print(
                f"SL    : {final_stop_loss:.2f}"
            )
            return

        # 1:3 Risk/Reward
        final_take_profit = (
            actual_entry
            + (risk * 3)
        )

    else:

        position_side = "SHORT"

        # SHORT:
        # SL = setup candle HIGH
        final_stop_loss = setup_high

        risk = (
            final_stop_loss
            - actual_entry
        )

        if risk <= 0:
            print("❌ Invalid SHORT setup-candle SL.")
            print(
                f"Entry : {actual_entry:.2f}"
            )
            print(
                f"SL    : {final_stop_loss:.2f}"
            )
            return

        # 1:3 Risk/Reward
        final_take_profit = (
            actual_entry
            - (risk * 3)
        )

    # ------------------------------------------------------
    # ROUND TO BTC PRICE TICK
    # ------------------------------------------------------

    if position_side == "LONG":
        final_stop_loss = round_price(
            final_stop_loss,
            "down"
        )
        final_take_profit = round_price(
            final_take_profit,
            "up"
        )
    else:
        final_stop_loss = round_price(
            final_stop_loss,
            "up"
        )
        final_take_profit = round_price(
            final_take_profit,
            "down"
        )

    # Recalculate after exchange tick rounding
    risk = abs(
        actual_entry
        - final_stop_loss
    )

    reward = abs(
        final_take_profit
        - actual_entry
    )

    actual_rr = (
        reward / risk
        if risk > 0
        else 0
    )

    print(
        "\n========== 15M S/R 1:3 TRADE PROTECTION =========="
    )
    print("Position       :", position_side)
    print("Quantity       :", abs(active_pos))
    print(
        f"Actual Entry   : {actual_entry:.2f}"
    )
    print(
        f"Setup Low      : {setup_low:.2f}"
    )
    print(
        f"Setup High     : {setup_high:.2f}"
    )
    print(
        f"Stop Loss      : {final_stop_loss:.2f}"
    )
    print(
        f"Risk           : {risk:.2f}"
    )
    print(
        f"Take Profit    : {final_take_profit:.2f}"
    )
    print(
        f"Reward         : {reward:.2f}"
    )
    print(
        f"Risk/Reward    : 1:{actual_rr:.2f}"
    )

    # ------------------------------------------------------
    # PLACE TP + SL
    # ------------------------------------------------------

    print(
        "\n🛡️ Placing TP + SL..."
    )

    tpsl_status, tpsl_response = (
        create_futures_tpsl(
            position_id=position_id,
            take_profit=final_take_profit,
            stop_loss=final_stop_loss,
            position_side=position_side
        )
    )

    print(
        "\n========== TP + SL RESPONSE =========="
    )
    print("STATUS   :", tpsl_status)
    print("RESPONSE :", tpsl_response)

    if tpsl_status not in (200, 201):

        print(
            "❌ TP + SL PLACEMENT FAILED."
        )

        print(
            "⚠️ POSITION MAY BE OPEN WITHOUT PROTECTION."
        )

        return

    print(
        "✅ TP + SL ACCEPTED."
    )

    print("\n" + "=" * 60)
    print("✅ LIVE TRADE SETUP COMPLETE")
    print("=" * 60)
    print("Signal   :", trade_signal)
    print("Position :", position_side)
    print(
        f"Entry    : {actual_entry:.2f}"
    )
    print(
        f"SL       : {final_stop_loss:.2f}"
    )
    print(
        f"TP       : {final_take_profit:.2f}"
    )
    print(
        f"RR       : 1:{actual_rr:.2f}"
    )
    print("Trailing : OFF")
    print("=" * 60)


    print("=" * 60)


# ==========================================================
# CONTINUOUS MODE
# ==========================================================

if __name__ == "__main__":

    print(
        "\n🔄 CONTINUOUS MODE:"
    )

    print(
        "Bot checks every 1 minute."
    )

    while True:

        try:

            run_bot()

        except Exception as e:

            print(
                "\n❌ BOT ERROR:",
                e
            )

        print(
            "\n⏳ Next 15M check..."
        )

        time.sleep(60)
