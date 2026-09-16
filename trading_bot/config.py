"""Default settings shared across the backtesting framework."""

# Ticker universe by asset class. yfinance ticker conventions:
#   stocks/ETFs -> plain symbols (AAPL, SPY)
#   futures     -> continuous contract symbols suffixed with "=F" (ES=F, CL=F, GC=F)
#   crypto      -> pair symbols suffixed with "-USD" (BTC-USD, ETH-USD)
UNIVERSE = {
    "stocks": ["AAPL", "MSFT", "SPY", "QQQ"],
    "futures": ["ES=F", "CL=F", "GC=F"],
    "crypto": ["BTC-USD", "ETH-USD"],
}

# yfinance intraday intervals are capped at 60 days of history and daily bars
# have no such limit, so the two timeframes need different lookback periods.
DAILY_PERIOD = "5y"
DAILY_INTERVAL = "1d"

INTRADAY_PERIOD = "60d"
INTRADAY_INTERVAL = "5m"

DEFAULT_CASH = 10_000
DEFAULT_COMMISSION = 0.001  # 0.1% per trade, a stand-in for spread/slippage/fees

CACHE_DIR = "data_cache"
RESULTS_DIR = "results"
