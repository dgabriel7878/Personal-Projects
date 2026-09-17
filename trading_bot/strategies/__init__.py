from trading_bot.strategies.absolute_momentum import AbsoluteMomentum
from trading_bot.strategies.accum_dist_trend import AccumDistTrend
from trading_bot.strategies.adx_dmi_trend import AdxDmiTrend
from trading_bot.strategies.awesome_oscillator_strategy import AwesomeOscillatorStrategy
from trading_bot.strategies.bollinger_mean_reversion import BollingerMeanReversion
from trading_bot.strategies.bollinger_squeeze_breakout import BollingerSqueezeBreakout
from trading_bot.strategies.cci_reversion import CciReversion
from trading_bot.strategies.chaikin_money_flow_strategy import ChaikinMoneyFlowStrategy
from trading_bot.strategies.donchian_breakout import DonchianBreakout
from trading_bot.strategies.ema_crossover import EmaCrossover
from trading_bot.strategies.fisher_transform_strategy import FisherTransformStrategy
from trading_bot.strategies.ichimoku_cloud import IchimokuCloud
from trading_bot.strategies.intraday_ema_trend import IntradayEmaTrend
from trading_bot.strategies.intraday_rsi_reversion import IntradayRsiReversion
from trading_bot.strategies.keltner_breakout import KeltnerBreakout
from trading_bot.strategies.linreg_trend import LinregTrend
from trading_bot.strategies.macd_momentum import MacdMomentum
from trading_bot.strategies.money_flow_index_reversion import MoneyFlowIndexReversion
from trading_bot.strategies.obv_trend import ObvTrend
from trading_bot.strategies.opening_range_breakout import OpeningRangeBreakout
from trading_bot.strategies.orb_bidirectional import OrbBidirectional
from trading_bot.strategies.parabolic_sar_strategy import ParabolicSarStrategy
from trading_bot.strategies.return_zscore_reversal import ReturnZscoreReversal
from trading_bot.strategies.roc_momentum import RocMomentum
from trading_bot.strategies.rsi2_connors import Rsi2MeanReversion
from trading_bot.strategies.rsi_mean_reversion import RsiMeanReversion
from trading_bot.strategies.sma200_trend_filter import Sma200TrendFilter
from trading_bot.strategies.sma_crossover import SmaCrossover
from trading_bot.strategies.stochastic_oscillator import StochasticOscillator
from trading_bot.strategies.supertrend_strategy import SupertrendStrategy
from trading_bot.strategies.triple_ma_alignment import TripleMaAlignment
from trading_bot.strategies.turn_of_month import TurnOfMonth
from trading_bot.strategies.turtle_soup import TurtleSoup
from trading_bot.strategies.vortex_trend import VortexTrend
from trading_bot.strategies.vwap_mean_reversion import VwapMeanReversion
from trading_bot.strategies.vwap_momentum import VwapMomentum
from trading_bot.strategies.williams_r_reversion import WilliamsRReversion

# Each entry: (display name, Strategy class, timeframe -- "daily" or "intraday")
STRATEGY_REGISTRY = [
    ("SMA Crossover", SmaCrossover, "daily"),
    ("RSI Mean Reversion", RsiMeanReversion, "daily"),
    ("Bollinger Mean Reversion", BollingerMeanReversion, "daily"),
    ("MACD Momentum", MacdMomentum, "daily"),
    ("Donchian Breakout", DonchianBreakout, "daily"),
    ("Opening Range Breakout", OpeningRangeBreakout, "intraday"),
    ("SMA200 Trend Filter", Sma200TrendFilter, "daily"),
    ("RSI(2) Connors Mean Reversion", Rsi2MeanReversion, "daily"),
    ("Supertrend", SupertrendStrategy, "daily"),
    ("Stochastic Oscillator", StochasticOscillator, "daily"),
    ("EMA Crossover", EmaCrossover, "daily"),
    ("Triple MA Alignment", TripleMaAlignment, "daily"),
    ("ADX/DMI Trend", AdxDmiTrend, "daily"),
    ("Ichimoku Cloud", IchimokuCloud, "daily"),
    ("Parabolic SAR", ParabolicSarStrategy, "daily"),
    ("Keltner Breakout", KeltnerBreakout, "daily"),
    ("Linear Regression Trend", LinregTrend, "daily"),
    ("ROC Momentum", RocMomentum, "daily"),
    ("Absolute Momentum (252d)", AbsoluteMomentum, "daily"),
    ("Williams %R Reversion", WilliamsRReversion, "daily"),
    ("CCI Reversion", CciReversion, "daily"),
    ("Return Z-Score Reversal", ReturnZscoreReversal, "daily"),
    ("Turtle Soup", TurtleSoup, "daily"),
    ("Bollinger Squeeze Breakout", BollingerSqueezeBreakout, "daily"),
    ("OBV Trend", ObvTrend, "daily"),
    ("Chaikin Money Flow", ChaikinMoneyFlowStrategy, "daily"),
    ("Accum/Dist Trend", AccumDistTrend, "daily"),
    ("Turn of Month", TurnOfMonth, "daily"),
    ("Awesome Oscillator", AwesomeOscillatorStrategy, "daily"),
    ("Fisher Transform", FisherTransformStrategy, "daily"),
    ("Money Flow Index Reversion", MoneyFlowIndexReversion, "daily"),
    ("Vortex Trend", VortexTrend, "daily"),
    ("VWAP Mean Reversion", VwapMeanReversion, "intraday"),
    ("Intraday RSI Reversion", IntradayRsiReversion, "intraday"),
    ("Intraday EMA Trend", IntradayEmaTrend, "intraday"),
    ("VWAP Momentum", VwapMomentum, "intraday"),
    ("ORB Bidirectional", OrbBidirectional, "intraday"),
]
