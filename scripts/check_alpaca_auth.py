#!/usr/bin/env python3
"""Minimal Alpaca connectivity check: confirms ALPACA_API_KEY/
ALPACA_SECRET_KEY in .env actually authenticate, independent of any
strategy/signal logic. Run this first whenever run_paper_trade.py
reports "unauthorized" -- it isolates whether the problem is your
credentials or something else.

Usage:
    python scripts/check_alpaca_auth.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from alpaca.trading.client import TradingClient

api_key = os.environ.get("ALPACA_API_KEY")
secret_key = os.environ.get("ALPACA_SECRET_KEY")

print("ALPACA_API_KEY loaded:   ", repr(api_key))
print("ALPACA_SECRET_KEY loaded:", repr(secret_key))

if not api_key or not secret_key:
    print("\nOne or both keys are missing/empty. Check that .env exists and has both lines filled in.")
    sys.exit(1)

client = TradingClient(api_key, secret_key, paper=True)

try:
    account = client.get_account()
    print(f"\nSUCCESS -- connected. Account status: {account.status}, equity: ${account.equity}")
except Exception as exc:
    print(f"\nFAILED to authenticate: {exc}")
    print(
        "\nMost likely cause: the key and secret don't match (e.g. you copied a new "
        "Key but kept an old Secret, or vice versa). Regenerate both together on "
        "https://app.alpaca.markets/paper/dashboard/overview and copy BOTH fresh "
        "values into .env at the same time."
    )
    sys.exit(1)
