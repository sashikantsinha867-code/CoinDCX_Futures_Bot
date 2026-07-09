import requests

PUBLIC_URL = "https://public.coindcx.com"

def get_candles(pair="B-BTC_USDT", interval="15m", limit=100):
    url = f"{PUBLIC_URL}/market_data/candles"

    params = {
        "pair": pair,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        print(response.text)
        return None