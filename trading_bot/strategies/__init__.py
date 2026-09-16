from trading_bot.strategies.bollinger_mean_reversion import BollingerMeanReversion
from trading_bot.strategies.donchian_breakout import DonchianBreakout
from trading_bot.strategies.macd_momentum import MacdMomentum
from trading_bot.strategies.opening_range_breakout import OpeningRangeBreakout
from trading_bot.strategies.rsi_mean_reversion import RsiMeanReversion
from trading_bot.strategies.sma_crossover import SmaCrossover

# Each entry: (display name, Strategy class, timeframe -- "daily" or "intraday")
STRATEGY_REGISTRY = [
    ("SMA Crossover", SmaCrossover, "daily"),
    ("RSI Mean Reversion", RsiMeanReversion, "daily"),
    ("Bollinger Mean Reversion", BollingerMeanReversion, "daily"),
    ("MACD Momentum", MacdMomentum, "daily"),
    ("Donchian Breakout", DonchianBreakout, "daily"),
    ("Opening Range Breakout", OpeningRangeBreakout, "intraday"),
]
