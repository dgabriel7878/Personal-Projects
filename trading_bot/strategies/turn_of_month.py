"""Turn-of-the-month seasonality: long only during the last few trading
days of each month plus the first few of the next, flat the rest of the
month. A well-documented calendar anomaly in equity index returns
(institutional flows, month-end rebalancing, payroll-driven buying)."""

import pandas as pd
from backtesting import Strategy


class TurnOfMonth(Strategy):
    first_n_days = 3
    last_n_days = 3

    def init(self):
        index = self.data.index
        periods = pd.PeriodIndex(index, freq="M")
        positions = pd.Series(range(len(index)), index=index)

        rank_from_start = positions.groupby(periods).cumcount() + 1
        days_in_month = positions.groupby(periods).transform("size")
        rank_from_end = days_in_month - rank_from_start + 1

        in_window = (rank_from_start <= self.first_n_days) | (rank_from_end <= self.last_n_days)
        self.in_window = in_window.values

    def next(self):
        i = len(self.data) - 1
        if not self.position and self.in_window[i]:
            self.buy()
        elif self.position and not self.in_window[i]:
            self.position.close()
