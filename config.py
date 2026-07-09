import os
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# ==========================
# CoinDCX API
# ==========================

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

# ==========================
# Trading Settings
# ==========================

SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
LEVERAGE = int(os.getenv("LEVERAGE", 5))
CAPITAL = float(os.getenv("CAPITAL", 5000))

RISK_PERCENT = float(os.getenv("RISK_PERCENT", 2))

PAPER_MODE = os.getenv("PAPER_MODE", "True").lower() == "true"

# Development Mode
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"

# ==========================
# API URLs
# ==========================

BASE_URL = "https://api.coindcx.com"
PUBLIC_URL = "https://public.coindcx.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")