# Backtested Trading Bot

Goal: find a trading strategy that actually holds up under backtesting
before risking any money, then move it through paper trading and finally a
live account. This repo is **Phase 1**: a framework to backtest and
objectively compare multiple strategies across stocks, futures, and crypto,
on both swing (daily) and intraday timeframes.

**Nothing in this repo places real trades yet.** It only backtests.

## How it fits together

```
trading_bot/
  config.py              # ticker universe, timeframes, cash/commission defaults
  data/loader.py          # OHLCV fetch (yfinance) + on-disk parquet cache
  strategies/              # one file per strategy, registered in __init__.py
  backtest/
    runner.py             # runs every strategy x every ticker, collects stats
    metrics.py            # extracts a clean stats row from a backtest run
scripts/
  run_backtests.py         # CLI: run everything, print + save a ranked comparison
results/                    # CSV output lands here (gitignored)
```

Backtests run on [backtesting.py](https://kernc.github.io/backtesting.py/),
a vectorized/event-driven engine that produces standard stats (Sharpe,
Sortino, max drawdown, win rate, profit factor, SQN, etc.) per run.

## Strategies included

| Strategy | Type | Timeframe | Idea |
|---|---|---|---|
| SMA Crossover | Trend-following | Daily | Fast SMA(20) crosses slow SMA(50) |
| RSI Mean Reversion | Mean reversion | Daily | Buy RSI(14) < 30, exit RSI > 55 |
| Bollinger Mean Reversion | Mean reversion | Daily | Buy at lower band, exit at the mean |
| MACD Momentum | Momentum | Daily | MACD line crosses its signal line |
| Donchian Breakout | Trend-following (Turtle-style) | Daily | Buy a 20-day high, exit a 10-day low |
| Opening Range Breakout | Breakout | Intraday (5m) | Buy a break above the first 15 minutes' range, flatten by session close |
| SMA200 Trend Filter | Trend-following (regime filter) | Daily | Long only while price is above its 200-day average |
| RSI(2) Connors Mean Reversion | Mean reversion | Daily | Buy RSI(2) < 10 only while above the 200-day average, exit RSI(2) > 70 |
| Supertrend | Trend-following (volatility-adaptive) | Daily | Long while the ATR-based Supertrend line signals an uptrend; risk-based sizing + hard ATR stop-loss |
| Stochastic Oscillator | Mean reversion | Daily | Buy %K crossing above %D from oversold, exit the reverse from overbought |
| EMA Crossover | Trend-following | Daily | Fast EMA(12) crosses slow EMA(26) |
| Triple MA Alignment | Trend-following (regime filter) | Daily | Long only while fast > mid > slow SMA (10/50/200) |
| ADX/DMI Trend | Trend-following + strength filter | Daily | Buy +DI/-DI cross, only when ADX confirms trend strength |
| Ichimoku Cloud | Trend-following | Daily | Buy Tenkan/Kijun cross while price is above the cloud |
| Parabolic SAR | Trend-following (trailing stop) | Daily | Long while the SAR dots trail below price |
| Keltner Breakout | Volatility breakout | Daily | Buy a close above the ATR-based upper Keltner band; risk-based sizing + hard ATR stop-loss |
| Linear Regression Trend | Trend-following (statistical) | Daily | Long while a rolling linear-regression slope is positive |
| ROC Momentum | Momentum | Daily | Long while the N-bar rate of change is positive |
| Absolute Momentum (252d) | Momentum (time-series) | Daily | Long while the trailing ~12-month return is positive |
| Williams %R Reversion | Mean reversion | Daily | Buy deeply oversold %R, exit once overbought |
| CCI Reversion | Mean reversion | Daily | Buy CCI < -100, exit CCI > 100 |
| Return Z-Score Reversal | Mean reversion (shock fade) | Daily | Buy after an unusually large down day (return z-score), exit once normalized |
| Turtle Soup | Contrarian (false-breakout fade) | Daily | Buy a failed break below the N-day low, exit after a fixed hold |
| Bollinger Squeeze Breakout | Volatility breakout | Daily | Buy an upper-band breakout following a low-volatility squeeze |
| OBV Trend | Volume | Daily | Buy when On-Balance Volume crosses above its own average |
| Chaikin Money Flow | Volume | Daily | Buy when Chaikin Money Flow crosses above zero |
| Accum/Dist Trend | Volume | Daily | Buy when the Accumulation/Distribution line crosses above its average |
| Turn of Month | Seasonality/calendar | Daily | Long only during the last/first few trading days of each month |
| Awesome Oscillator | Momentum | Daily | Buy when the histogram crosses above zero |
| Fisher Transform | Momentum (turning points) | Daily | Buy when the Fisher line crosses its lagged signal |
| Money Flow Index Reversion | Mean reversion (volume-weighted) | Daily | Buy MFI < 20, exit MFI > 80 |
| Vortex Trend | Trend-following | Daily | Buy +VI/-VI crossover |

These are well-known, widely documented approaches -- not proprietary
alpha. The point of this phase is to measure, with real cost assumptions
(commission/slippage baked into every run), whether any of them actually
produces a positive, risk-adjusted edge on the markets you care about, and
to compare them on equal footing rather than picking one on vibes.

## Asset universe

Configured in `trading_bot/config.py`. yfinance ticker conventions:

- **Stocks/ETFs**: plain symbols (`AAPL`, `SPY`, `QQQ`)
- **Futures**: continuous contracts (`ES=F`, `CL=F`, `GC=F`)
- **Crypto**: pair symbols (`BTC-USD`, `ETH-USD`)

Daily strategies pull 5 years of daily bars; intraday strategies pull 60
days of 5-minute bars (yfinance's intraday history limit).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running backtests

```bash
# Everything: all asset classes, both timeframes
python scripts/run_backtests.py

# Narrow it down
python scripts/run_backtests.py --asset-classes stocks crypto
python scripts/run_backtests.py --timeframes daily
python scripts/run_backtests.py --cash 25000 --commission 0.0005
```

This prints a per-run results table (one row per strategy x ticker) and a
ranked summary (strategies sorted by average Sharpe Ratio across every
market tested), and saves both as timestamped CSVs under `results/`.

## Validating a strategy out-of-sample

A backtest over one fixed history can look great purely because its
parameters were (unintentionally) tuned to that exact history. Before
trusting a strategy from the ranking above, walk-forward validate it: the
tool below optimizes its parameters on the first `--train-frac` of each
ticker's history, then runs those exact parameters, unmodified, on the
remaining unseen period.

```bash
python scripts/validate_strategy.py --strategy "Donchian Breakout" --tickers AAPL SPY QQQ GC=F
python scripts/validate_strategy.py --strategy "RSI Mean Reversion" --train-frac 0.6
```

Only strategies with a parameter grid registered in
`trading_bot/backtest/validate.py`'s `PARAM_GRIDS` can be validated this
way (currently all of them). If most tickers keep a positive out-of-sample
Sharpe with their in-sample-optimized parameters, that's real evidence of
an edge. If most go negative or flip sign, the in-sample backtest was
likely curve-fit, not a tradable edge.

## Interpreting the output

Don't just chase total return. Look at, in rough order of importance:

- **Sharpe / Sortino Ratio** -- return per unit of risk; the primary
  ranking metric. Below ~0.5-1.0 on a multi-year backtest generally isn't
  worth trading.
- **Max Drawdown** -- the worst peak-to-trough loss. A strategy with a
  great return but a 50% drawdown is not survivable emotionally or
  financially.
- **Win Rate** and **Profit Factor** -- a strategy can be profitable with
  a low win rate if winners are much bigger than losers (trend-following),
  or need a high win rate if it's a mean-reversion strategy with small
  edges.
- **# Trades** -- too few trades (e.g. under ~30) means the stats aren't
  statistically meaningful; too many relative to the period can mean
  commissions are eating the edge.
- Compare **Return [%] vs. Buy & Hold Return [%]** -- a strategy that
  can't beat buying and holding the same asset isn't adding value.

A strategy that looks great on one ticker but falls apart on the others
tested is probably overfit to that ticker's specific history, not a real
edge.

## Adding a new strategy

1. Create `trading_bot/strategies/my_strategy.py` with a class subclassing
   `backtesting.Strategy` (see any existing strategy for the pattern).
2. Register it in `trading_bot/strategies/__init__.py`'s
   `STRATEGY_REGISTRY`, tagged `"daily"` or `"intraday"`.
3. Run `python scripts/run_backtests.py` -- it's automatically included in
   the comparison.

## Roadmap

- **Phase 1 (this repo, in progress)**: backtest and rank strategies
  across markets; iterate on parameters until one shows a consistent,
  robust edge net of costs (not just a lucky curve-fit on one ticker/date
  range).
- **Phase 2**: wire the winning strategy into a live-data loop against an
  **Alpaca paper trading account** (free, real-time fills, zero real
  money at risk) via their REST/websocket API, and run it for a
  meaningful sample period before trusting it.
- **Phase 3**: once the paper account confirms the edge survives real
  execution (slippage, fills, latency, live data quirks), move a small
  amount of real capital, with strict position sizing and a kill switch.
- **Possible future addition -- macro regime filter**: an overlay like
  "only trade long while the VIX is below X" or "while the yield curve
  isn't inverted" is buildable with free historical data (VIX via
  yfinance, rates via FRED), but requires merging a second data series
  into the backtest -- every strategy above trades on a single asset's own
  OHLCV only, so this is an architecture change, not a drop-in strategy.
  Not started.
- **Deliberately not pursued (for now) -- news/sentiment signals**:
  backtesting a real news- or sentiment-driven strategy needs historical
  news/sentiment data, and the reliable sources (RavenPack, Bloomberg) are
  paid; free alternatives (GDELT, NewsAPI) are thin on history or quality.
  This is a materially bigger, separate undertaking, not a natural
  extension of the technical-indicator strategies here.

**Disclaimer**: a strategy that backtests well is not a guarantee of
future performance -- markets change, and backtests are prone to overfitting
and survivorship bias. Treat every "proven" result here as a hypothesis to
keep testing, not a fact. Only risk money you can afford to lose, and size
up gradually even after a successful paper-trading run.
