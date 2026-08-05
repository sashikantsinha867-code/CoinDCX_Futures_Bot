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

# ==========================
# TRAILING STOP SETTINGS
# ==========================

TRAILING_STOP = True

# Trailing start after profit moves by this many ATRs
TRAILING_TRIGGER_ATR = 1.0

# Distance of trailing SL from current price (in ATR)
TRAILING_DISTANCE_ATR = 0.8

# Break-even after profit moves by this many ATRs
BREAK_EVEN_ENABLED = True
BREAK_EVEN_TRIGGER_ATR = 1.0

