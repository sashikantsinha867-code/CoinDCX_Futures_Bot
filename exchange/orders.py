import requests
from decimal import Decimal, ROUND_DOWN, ROUND_UP

from config import BASE_URL, LEVERAGE, FUTURES_MARGIN
from exchange.auth import authenticated_headers, timestamp


FUTURES_PAIR = "B-BTC_USDT"


def get_balances():
    body = {"timestamp": timestamp()}
    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/users/balances",
        data=payload,
        headers=headers,
        timeout=10
    )

    return response.status_code, response.json()


def get_futures_wallet():
    """
    Get CoinDCX Futures wallet details.

    Returns the wallet matching FUTURES_MARGIN
    (INR or USDT).
    """

    body = {
        "timestamp": timestamp()
    }

    headers, payload = authenticated_headers(body)

    response = requests.get(
        f"{BASE_URL}/exchange/v1/derivatives/futures/wallets",
        data=payload,
        headers=headers,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        return response.status_code, {
            "raw_response": response.text
        }

    return response.status_code, data


def get_futures_available_balance():
    """
    Return the Futures wallet balance for the configured
    margin currency.

    This function is READ-ONLY and does not place an order.
    """

    status, data = get_futures_wallet()

    if status != 200:
        return status, 0.0, data

    wallets = data if isinstance(data, list) else data.get("data", data)

    if not isinstance(wallets, list):
        return status, 0.0, data

    for wallet in wallets:
        if wallet.get("currency_short_name") == FUTURES_MARGIN:
            balance = float(wallet.get("balance", 0) or 0)
            locked = float(wallet.get("locked_balance", 0) or 0)

            # For isolated INR/USDT wallet, the immediately
            # usable balance is the wallet balance after
            # already locked margin.
            available = max(balance - locked, 0.0)

            return status, available, wallet

    return status, 0.0, {
        "error": f"{FUTURES_MARGIN} Futures wallet not found",
        "wallets": wallets
    }



def get_usdt_inr_conversion_rate():
    """
    Get CoinDCX USDT/INR conversion price
    for INR-margined Futures.

    READ-ONLY: does not place any order.
    """

    body = {
        "timestamp": timestamp()
    }

    headers, payload = authenticated_headers(body)

    response = requests.get(
        f"{BASE_URL}/api/v1/derivatives/futures/data/conversions",
        data=payload,
        headers=headers,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        return response.status_code, 0.0, {
            "raw_response": response.text
        }

    if response.status_code != 200:
        return response.status_code, 0.0, data

    conversions = data if isinstance(data, list) else data.get("data", data)

    if not isinstance(conversions, list):
        return response.status_code, 0.0, data

    for item in conversions:
        if (
            item.get("symbol") == "USDTINR"
            and item.get("margin_currency_short_name") == "INR"
            and item.get("target_currency_short_name") == "USDT"
        ):
            rate = float(item.get("conversion_price", 0) or 0)

            if rate > 0:
                return response.status_code, rate, item

    return response.status_code, 0.0, {
        "error": "USDTINR conversion rate not found",
        "conversions": conversions
    }



def get_futures_instrument_details():
    """
    Fetch live CoinDCX Futures instrument rules for B-BTC_USDT.

    READ-ONLY:
    - quantity_increment
    - min_quantity
    - max_quantity
    - min_trade_size
    - min_notional
    - price_increment
    - target precision
    """

    response = requests.get(
        f"{BASE_URL}/exchange/v1/derivatives/futures/data/instrument",
        params={
            "pair": FUTURES_PAIR,
            "margin_currency_short_name": FUTURES_MARGIN,
        },
        timeout=10,
    )

    try:
        data = response.json()
    except ValueError:
        return response.status_code, {}

    if response.status_code != 200:
        return response.status_code, data

    instrument = data.get("instrument", data)

    if not isinstance(instrument, dict):
        return response.status_code, {}

    return response.status_code, instrument


def place_futures_market_order(
    side,
    pair=FUTURES_PAIR,
    quantity=0,
    leverage=None
):
    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")

    quantity = Decimal(str(quantity))

    MIN_QUANTITY = Decimal("0.001")
    QUANTITY_STEP = Decimal("0.001")

    if quantity < MIN_QUANTITY:
        raise ValueError(
            f"BTC Futures minimum quantity is {MIN_QUANTITY}"
        )

    quantity = (
        quantity / QUANTITY_STEP
    ).to_integral_value(rounding=ROUND_DOWN) * QUANTITY_STEP

    quantity = float(quantity)

    if leverage is None:
        leverage = LEVERAGE

    body = {
        "timestamp": timestamp(),
        "order": {
            "side": side,
            "pair": pair,
            "order_type": "market_order",
            "total_quantity": quantity,
            "leverage": int(leverage),
            "notification": "no_notification",
            "hidden": False,
            "post_only": False,
            "margin_currency_short_name": FUTURES_MARGIN
        }
    }

    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/derivatives/futures/orders/create",
        data=payload,
        headers=headers,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "raw_response": response.text,
            "content_type": response.headers.get("content-type"),
        }

    return response.status_code, data



def get_futures_orders(
    status="open,filled,partially_filled,cancelled,rejected",
    pair=FUTURES_PAIR,
    size="20"
):
    """
    Fetch Futures orders for the configured pair/margin.
    Used to confirm that a newly-created market order
    has actually been filled before placing TP.
    """

    body = {
        "timestamp": timestamp(),
        "status": status,
        "page": "1",
        "size": size,
        "pairs": pair,
        "margin_currency_short_name": [FUTURES_MARGIN],
    }

    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/derivatives/futures/orders",
        data=payload,
        headers=headers,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "raw_response": response.text
        }

    return response.status_code, data


def get_futures_positions():
    """
    Get BTC Futures position for the configured margin currency.

    CoinDCX defaults this endpoint to USDT margin if
    margin_currency_short_name is omitted, so INR must be
    explicitly supplied when FUTURES_MARGIN=INR.
    """

    body = {
        "timestamp": timestamp(),
        "page": "1",
        "size": "20",
        "pairs": FUTURES_PAIR,
        "margin_currency_short_name": [FUTURES_MARGIN],
    }

    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/derivatives/futures/positions",
        data=payload,
        headers=headers,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "raw_response": response.text
        }

    return response.status_code, data




def create_futures_tpsl(
    position_id,
    take_profit,
    stop_loss=None,
    position_side=None
):
    # CoinDCX B-BTC_USDT price increment = 0.1
    tick = Decimal("0.1")

    # TP rounding:
    # LONG  -> round UP
    # SHORT -> round DOWN
    tp_rounding = (
        ROUND_UP
        if position_side == "LONG"
        else ROUND_DOWN
    )

    tp = (
        Decimal(str(take_profit))
        / tick
    ).quantize(
        Decimal("1"),
        rounding=tp_rounding
    ) * tick

    tp_str = format(tp, "f")

    body = {
        "timestamp": timestamp(),
        "id": str(position_id),
        "take_profit": {
            "stop_price": tp_str,
            "order_type": "take_profit_market"
        }
    }

    # Add SL only when explicitly supplied.
    if stop_loss is not None:

        # SL rounding:
        # LONG  -> round DOWN
        # SHORT -> round UP
        sl_rounding = (
            ROUND_DOWN
            if position_side == "LONG"
            else ROUND_UP
        )

        sl = (
            Decimal(str(stop_loss))
            / tick
        ).quantize(
            Decimal("1"),
            rounding=sl_rounding
        ) * tick

        sl_str = format(sl, "f")

        body["stop_loss"] = {
            "stop_price": sl_str,
            "order_type": "stop_market"
        }

    print("\n========== COINDCX TPSL PAYLOAD ==========")
    print("Position ID :", body["id"])
    print("TP          :", tp_str)

    if stop_loss is None:
        print("SL          : NONE")
    else:
        print("SL          :", sl_str)

    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/derivatives/futures/positions/create_tpsl",
        data=payload,
        headers=headers,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "raw_response": response.text
        }

    return response.status_code, data


# ==========================================================
# SAFE TRAILING ORDER HELPERS
# ==========================================================
