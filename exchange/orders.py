import requests

from config import BASE_URL
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