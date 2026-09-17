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
| VWAP Mean Reversion | Mean reversion (bidirectional) | Intraday (5m) | Long/short on reversion to session VWAP; flattens by close |
| Intraday RSI Reversion | Mean reversion (bidirectional) | Intraday (5m) | Long/short on RSI oversold/overbought; flattens by close |

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

## Paper trading (Phase 2)

Two live paper-trading setups exist, against a free **Alpaca paper
trading account** (real-time fills, zero real money at risk). Both are
scoped to US stocks/ETFs, since that's what Alpaca's standard equities
API supports cleanly (whole-share orders, a contingent stop-loss leg);
crypto and futures aren't wired up in either.

### Setup (shared by both)

1. Sign up free at [alpaca.markets](https://alpaca.markets), switch to
   **Paper Trading** in the dashboard sidebar, and generate an API key
   pair from there (not the live-trading dashboard).
2. `cp .env.example .env` and fill in `ALPACA_API_KEY` /
   `ALPACA_SECRET_KEY`. `.env` is gitignored -- never commit real keys.
   If auth ever fails, run `python scripts/check_alpaca_auth.py` first
   to isolate whether it's a credentials problem before debugging
   anything else.

### Intraday (long + short, active strategy)

`trading_bot/execution/intraday_trader.py` trades the VWAP Mean
Reversion or Intraday RSI Reversion strategy (choose with `--strategy
vwap` or `--strategy rsi`) -- both bidirectional, both flatten before
the close, neither holds overnight. This is the **currently active**
live strategy.

Unlike the daily setup below, this needs to be invoked repeatedly
throughout market hours, not once after close, since these strategies
react to intraday price action. Each invocation computes the latest
signal from fresh 5-minute bars, decides long / short / exit / hold, and
reconciles it against your live position -- opening a risk-sized
position with a hard ATR stop-loss, closing/covering on a reversion
signal, or force-flattening in the last ~10 minutes before the close
regardless of signal.

```bash
# dry-run first
python scripts/run_intraday_trade.py --symbols AAPL MSFT SPY QQQ --strategy vwap --dry-run
# then for real
python scripts/run_intraday_trade.py --symbols AAPL MSFT SPY QQQ --strategy vwap
```

**Scheduling** -- two options, depending on whether you want this running
on your own machine or fully in the cloud.

#### Option A: local cron (your computer has to be on)

```bash
# crontab -e (macOS/Linux) -- runs :30-:55 past each hour, 9am-4pm local
# adjust the hour range for your timezone vs. market hours (9:30-16:00 ET)
*/5 9-16 * * 1-5 cd /path/to/Personal-Projects && .venv/bin/python scripts/run_intraday_trade.py --symbols AAPL MSFT SPY QQQ --strategy vwap >> intraday_trade.log 2>&1
```

If your laptop is asleep, off, or disconnected when a run is due, that
cycle simply doesn't happen -- no queueing, no catch-up.

#### Option B: GitHub Actions (runs in the cloud, no computer needed)

`.github/workflows/intraday_trading.yml` runs the same script on a cron
schedule inside GitHub's own infrastructure -- your computer doesn't need
to be on at all. `.github/workflows/daily_summary.yml` runs once after
the close and commits a readable report to `logs/summary_<date>.md` in
the repo, so you can open GitHub at the end of the day and see exactly
what happened without digging through logs.

**One-time setup:**
1. Add your Alpaca keys as encrypted repo secrets: repo **Settings ->
   Secrets and variables -> Actions -> Secrets tab -> New repository
   secret**, add `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`.
2. **Important if your repo is private**: GitHub Actions gives private
   repos only 2,000 free minutes/month. A job every 5 minutes for ~9
   market hours a day, 5 days/week, can use 2,300-7,000+ minutes/month
   depending on setup overhead -- likely more than the free tier. Public
   repos get **unlimited** free Actions minutes, which is why we made
   this one public. If you'd rather keep it private, either widen the
   cron interval in `.github/workflows/intraday_trading.yml` (e.g. every
   15 minutes) or accept that it may stop running partway through the
   month once the free quota is used (it fails safely -- GitHub doesn't
   silently bill you for it unless you've added a payment method for
   overages -- but the automation goes quiet, which you'd need to notice).
3. Both workflows default to `workflow_dispatch`, so you can trigger a
   test run by hand from the repo's **Actions** tab before waiting for
   the schedule.
4. **Dry-run by default.** The trading workflow only places real orders
   if the repo variable `DRY_RUN` is set to exactly `false` (**Settings
   -> Secrets and variables -> Actions -> Variables tab -> New repository
   variable**, name `DRY_RUN`, value `false`). Leaving it unset, or any
   other value, keeps it in dry-run mode -- check the Actions run logs
   for a few cycles before flipping this.

`scripts/daily_summary.py` (what the summary workflow runs) can also be
run manually anytime, locally or via the Actions tab, for an on-demand
snapshot of today's filled orders, open positions, and day P&L:
```bash
python scripts/daily_summary.py
```

**What's been verified vs. not**: the full decision logic (long entry,
short entry, signal-based exit for both directions, the forced
end-of-day flatten, and the market-closed skip) was tested against a
mocked Alpaca client covering every branch, and two real bugs were
caught and fixed this way -- risk-based sizing had no leverage cap, so a
tight intraday stop could silently demand a position bigger than the
account could afford and the order would just never fill (this also
turned out to over-commit capital when trading several symbols in one
run, fixed by splitting the cap across the batch); and `rsi()` returned
`NaN` instead of 100 on a lookback window with zero losses. What's
**not** verified is the real Alpaca API response to an actual
short-sale order (whether the stop-loss leg correctly becomes a
buy-to-cover), or the GitHub Actions workflows themselves (YAML syntax
was validated locally, but never actually run -- this sandbox has no
network access to Alpaca or a way to trigger real Actions runs). Watch
your first few short trades and your first few cloud runs closely.

Two intraday strategies are backtestable but neither has been walk-forward
validated the way Supertrend/Keltner Breakout were on daily data --
yfinance only gives 60 days of 5-minute history, a thin sample for a
strategy trading every day. Run both through `scripts/run_backtests.py`
and `scripts/validate_strategy.py` before trusting either with real
conviction; `--strategy vwap` is the default here only because it was
asked for first, not because it's been shown to be better.

### Daily (Supertrend, long-only)

`trading_bot/execution/alpaca_trader.py` + `scripts/run_paper_trade.py`
still exist and work the same way as before -- trading Supertrend
long-only, once per trading day after close:

```bash
python scripts/run_paper_trade.py --symbols AAPL MSFT SPY QQQ --dry-run
```
```bash
# crontab -e -- 4:30pm local time, weekdays; adjust for your timezone
30 16 * * 1-5 cd /path/to/Personal-Projects && .venv/bin/python scripts/run_paper_trade.py --symbols AAPL MSFT SPY QQQ >> paper_trade.log 2>&1
```

This is no longer the actively-traded strategy (superseded by the
intraday setup above per a deliberate choice to trade more frequently
and both directions), but the code is left in place since Supertrend
remains the most out-of-sample-validated strategy in this repo.

## Roadmap

- **Phase 1 (done, ongoing)**: backtest, rank, and out-of-sample validate
  strategies across markets. 34 strategies tested on daily/swing
  timeframes; **Supertrend** is the current leader there (9/9 tickers
  positive out-of-sample), with **Keltner Breakout** a close second
  (8/9). The two intraday strategies (VWAP Mean Reversion, Intraday RSI
  Reversion) are backtestable but not yet walk-forward validated --
  yfinance's 60-day intraday history is thin for that. Keep revisiting
  as new strategies, longer histories, or better intraday data become
  available.
- **Phase 2 (built, needs live testing)**: two live setups exist against
  a free **Alpaca paper trading account** (see "Paper trading" above).
  The **intraday, bidirectional setup is currently the active one** --
  a deliberate switch from the originally-live daily Supertrend, in
  favor of trading more frequently and both long and short. Both setups'
  reconciliation logic is verified against a mocked client (a real
  leverage-sizing bug and an RSI edge case were caught this way before
  either went near a live account), but neither has been exercised
  against Alpaca's real API from this environment (no network access
  here) -- run intraday with `--dry-run` first and watch closely,
  especially the first real short trade.
- **Possible follow-up -- longer intraday history**: Alpaca's own market
  data API likely gives more than yfinance's 60-day cap on 5-minute
  bars, which would make walk-forward validating the intraday strategies
  actually meaningful. Not built; flagged as a real gap, not resolved.
- **Phase 3**: once a paper account confirms an edge survives real
  execution (slippage, fills, latency, live data quirks) for a
  meaningful sample period, move a small amount of real capital, with
  strict position sizing and a kill switch.
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
