"""Daily stock scanner: narrows the full market down to a short list of
symbols worth pointing an intraday strategy at today, using two of
Alpaca's data endpoints (same account/keys already used for paper
trading, no separate API/key needed):

  - Screener API: today's most active stocks by volume/trade count, and
    today's biggest gainers/losers by percent move.
  - News API: how many news articles have been published about each
    candidate recently, as a rough "does this stock have a catalyst
    today" signal.

This module answers "what should we even be looking at today" -- it does
NOT predict direction and has no backtested return of its own. A strategy
still has to find and time the actual entry/exit. Do not wire this into a
live/scheduled workflow until whatever strategy trades its output has
real, validated out-of-sample edge (see trading_bot/backtest/validate.py)
-- the same rule that applies to any strategy applies to what feeds it.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from alpaca.data.enums import MarketType, MostActivesBy
from alpaca.data.historical.news import NewsClient
from alpaca.data.historical.screener import ScreenerClient
from alpaca.data.requests import MarketMoversRequest, MostActivesRequest, NewsRequest


def get_screener_client() -> ScreenerClient:
    return ScreenerClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])


def get_news_client() -> NewsClient:
    return NewsClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])


def most_active_symbols(client: ScreenerClient, top_n: int = 30, by: MostActivesBy = MostActivesBy.VOLUME):
    """Today's top_n most active stocks by `by` (volume or trade count) --
    a broad, liquid candidate pool ranked by how much is actually trading
    in each name today, not by how much it has moved."""
    result = client.get_most_actives(MostActivesRequest(top=top_n, by=by))
    return list(result.most_actives)


def top_movers(client: ScreenerClient, top_n: int = 15):
    """Today's biggest gainers and losers by percent change -- returns
    (gainers, losers), each a list of Mover objects."""
    result = client.get_market_movers(MarketMoversRequest(market_type=MarketType.STOCKS, top=top_n))
    return list(result.gainers), list(result.losers)


def news_counts(client: NewsClient, symbols: list[str], lookback_hours: int = 18) -> dict[str, int]:
    """Number of news articles published for each symbol in the last
    `lookback_hours` -- a rough proxy for "has a fresh catalyst today"."""
    if not symbols:
        return {}
    start = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    request = NewsRequest(symbols=",".join(symbols), start=start, limit=50, exclude_contentless=True)
    news_set = client.get_news(request)
    counts = {s: 0 for s in symbols}
    for article in news_set.data.get("news", []):
        for s in article.symbols:
            if s in counts:
                counts[s] += 1
    return counts


def rank_candidates(top_n: int = 15, active_pool: int = 40, news_lookback_hours: int = 18) -> list[dict]:
    """Builds today's watchlist: pulls the `active_pool` most active
    stocks plus the top gainers/losers, tags each with its news-article
    count, and ranks the union with liquid + newsworthy names first.

    Returns a list of dicts (most active `top_n` symbols) sorted with:
      1. has_catalyst (any recent news) first,
      2. |percent_change| (bigger intraday move first) as the tiebreak,
      3. volume as the final tiebreak.
    Each dict: symbol, volume, trade_count, percent_change (may be None
    if the symbol wasn't in the gainers/losers list), news_count,
    has_catalyst.
    """
    screener = get_screener_client()
    news = get_news_client()

    actives = most_active_symbols(screener, top_n=active_pool)
    gainers, losers = top_movers(screener, top_n=active_pool)
    percent_change = {m.symbol: m.percent_change for m in gainers + losers}

    candidates = {a.symbol: {"volume": a.volume, "trade_count": a.trade_count} for a in actives}
    for symbol, change in percent_change.items():
        candidates.setdefault(symbol, {"volume": None, "trade_count": None})

    counts = news_counts(news, list(candidates), news_lookback_hours)

    ranked = [
        {
            "symbol": symbol,
            "volume": info["volume"],
            "trade_count": info["trade_count"],
            "percent_change": percent_change.get(symbol),
            "news_count": counts.get(symbol, 0),
            "has_catalyst": counts.get(symbol, 0) > 0,
        }
        for symbol, info in candidates.items()
    ]
    ranked.sort(
        key=lambda r: (
            r["has_catalyst"],
            abs(r["percent_change"]) if r["percent_change"] is not None else 0.0,
            r["volume"] or 0.0,
        ),
        reverse=True,
    )
    return ranked[:top_n]
