import hashlib
import hmac
import json
import time

from config import API_KEY, API_SECRET


def create_signature(body):
    payload = json.dumps(body, separators=(",", ":"))

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return payload, signature


def authenticated_headers(body):
    payload, signature = create_signature(body)

    headers = {
        "Content-Type": "application/json",
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
    }

    return headers, payload


def timestamp():
    return int(time.time() * 1000)