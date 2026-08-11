import requests

from config import BASE_URL, LEVERAGE, FUTURES_MARGIN
from exchange.auth import authenticated_headers, timestamp


def get_balances():
    body = {
        "timestamp": timestamp()
    }

    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/users/balances",
        data=payload,
        headers=headers,
        timeout=10
    )

    return response.status_code, response.json()


def place_futures_market_order(
    side,
    pair,
    quantity,
    leverage=None
):
    """
    LIVE Futures market order.

    This function is only called when bot.py explicitly
    chooses LIVE MODE.
    """

    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")

    quantity = float(quantity)

    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    if leverage is None:
        leverage = LEVERAGE

    body = {
        "side": side,
        "pair": pair,
        "order_type": "market_order",
        "total_quantity": quantity,
        "leverage": int(leverage),
        "margin_currency_short_name": FUTURES_MARGIN,
        "notification": "no_notification",
        "time_in_force": "good_till_cancel",
        "hidden": False,
        "post_only": False,
        "timestamp": timestamp()
    }

    headers, payload = authenticated_headers(body)

    response = requests.post(
        f"{BASE_URL}/exchange/v1/derivatives/futures/orders/create",
        data=payload,
        headers=headers,
        timeout=10
    )

    return response.status_code, response.json()
