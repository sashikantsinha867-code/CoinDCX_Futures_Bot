import json
import os

PORTFOLIO_FILE = "database/portfolio.json"


def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return {
            "balance": 5000,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0
        }

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=4)


def update_portfolio(pnl):

    portfolio = load_portfolio()

    portfolio["balance"] += pnl
    portfolio["total_trades"] += 1
    portfolio["total_pnl"] += pnl

    if pnl > 0:
        portfolio["wins"] += 1
    else:
        portfolio["losses"] += 1

    save_portfolio(portfolio)

    return portfolio