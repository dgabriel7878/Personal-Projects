#!/usr/bin/env python3
"""End-of-day summary of today's trading activity: orders filled, current
open positions, and day P&L, pulled from your Alpaca paper account.
Meant to run once shortly after market close.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment -- copy
.env.example to .env and fill in your Alpaca **paper trading** keys.
"""

import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest

ET = ZoneInfo("America/New_York")


def get_client() -> TradingClient:
    api_key = os.environ["ALPACA_API_KEY"]
    secret_key = os.environ["ALPACA_SECRET_KEY"]
    return TradingClient(api_key, secret_key, paper=True)


def todays_filled_orders(client: TradingClient):
    today_et = datetime.now(ET).date()
    # Cast a wide net (last 24h by submit time) then filter precisely by
    # fill time in ET, since "today" by UTC date would be wrong near
    # midnight UTC (which falls mid-afternoon/evening ET).
    request = GetOrdersRequest(
        status=QueryOrderStatus.CLOSED,
        after=datetime.now(ZoneInfo("UTC")) - timedelta(hours=30),
        direction="asc",
        limit=200,
    )
    orders = client.get_orders(request)
    return [
        o for o in orders
        if o.filled_at is not None and o.filled_at.astimezone(ET).date() == today_et
    ]


def build_summary(client: TradingClient) -> str:
    account = client.get_account()
    equity = float(account.equity)
    last_equity = float(account.last_equity)
    day_pnl = equity - last_equity
    day_pnl_pct = (day_pnl / last_equity * 100) if last_equity else 0.0

    filled_orders = todays_filled_orders(client)
    positions = client.get_all_positions()

    lines = []
    lines.append(f"=== Daily Summary -- {datetime.now(ET).strftime('%Y-%m-%d')} ===")
    lines.append("")
    sign = "+" if day_pnl >= 0 else ""
    lines.append(f"Account equity: ${equity:,.2f}  (yesterday's close: ${last_equity:,.2f})")
    lines.append(f"Day P&L: {sign}${day_pnl:,.2f} ({sign}{day_pnl_pct:.2f}%)")
    lines.append("")

    lines.append(f"=== Orders filled today ({len(filled_orders)}) ===")
    if not filled_orders:
        lines.append("(none)")
    else:
        for o in filled_orders:
            filled_time = o.filled_at.astimezone(ET).strftime("%H:%M:%S")
            side = o.side.value.upper()
            price = float(o.filled_avg_price) if o.filled_avg_price else 0.0
            lines.append(f"  {filled_time} ET  {side:5s} {o.filled_qty} {o.symbol} @ ${price:.2f}")
    lines.append("")

    lines.append(f"=== Current open positions ({len(positions)}) ===")
    if not positions:
        lines.append("(none -- flat)")
    else:
        for p in positions:
            side = p.side.value if hasattr(p.side, "value") else str(p.side)
            pl = float(p.unrealized_pl)
            pl_pct = float(p.unrealized_plpc) * 100
            pl_sign = "+" if pl >= 0 else ""
            lines.append(
                f"  {p.symbol}: {side.upper()} {p.qty} shares, avg entry ${float(p.avg_entry_price):.2f}, "
                f"current ${float(p.current_price):.2f}, unrealized P&L {pl_sign}${pl:,.2f} ({pl_sign}{pl_pct:.2f}%)"
            )

    return "\n".join(lines)


def main():
    if "ALPACA_API_KEY" not in os.environ or "ALPACA_SECRET_KEY" not in os.environ:
        print(
            "Missing ALPACA_API_KEY / ALPACA_SECRET_KEY.\n"
            "Copy .env.example to .env and fill in your paper trading keys from "
            "https://app.alpaca.markets/paper/dashboard/overview"
        )
        sys.exit(1)

    client = get_client()
    print(build_summary(client))


if __name__ == "__main__":
    main()
