
import os
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
US_BUSINESS_DAY = CustomBusinessDay(calendar=USFederalHolidayCalendar())
from os.path import exists
import pandas as pd
from backtesting import Strategy
from backtesting import Backtest
import pandas_ta as ta
from ta.utils import *
import math


"""
Based on
https://www.tradingview.com/script/q23anHmP-VuManChu-Swing-Free/
"""


DATA_PATH = "C:\\dev\\trading\\tradesystem1\\data\\crypto"


def range_size(df: pd.DataFrame, range_period: float, range_multiplier: int):
    wper = range_period * 2 - 1
    # last candle is last index, not 0
    average_range = ta.ema(df.diff().abs(), range_period)
    AC = ta.ema(average_range, wper) * range_multiplier
    return AC


def range_filter(x: pd.DataFrame, r: pd.DataFrame) -> pd.DataFrame:
    range_filt = x.copy()
    hi_band = x.copy()
    lo_band = x.copy()

    for i in range(x.size):
        if i < 1:
            continue
        if math.isnan(r[i]):
            continue
        if x[i] > nz(range_filt[i - 1]):
            if x[i] - r[i] < nz(range_filt[i - 1]):
                range_filt[i] = nz(range_filt[i - 1])
            else:
                range_filt[i] = x[i] - r[i]
        else:
            if x[i] + r[i] > nz(range_filt[i - 1]):
                range_filt[i] = nz(range_filt[i - 1])
            else:
                range_filt[i] = x[i] + r[i]

        hi_band[i] = range_filt[i] + r[i]
        lo_band[i] = range_filt[i] - r[i]

    return hi_band, lo_band, range_filt


def nz(x) -> float:
    res = x
    if math.isnan(x):
        res = 0.0

    return res


def vumanchu_swing(df, swing_period, swing_multiplier):
    smrng = range_size(df['Close'], swing_period, swing_multiplier)
    hi_band, lo_band, range_filt = range_filter(df['Close'], smrng)
    return range_filt


class MixedStrategy(Strategy):
    ema_period_1 = 50
    ema_period_2 = 200
    ema_lookback = 50

    swing_period = 20
    swing_multiplier = 3.5

    stop_loss_percent = 15

    last_purchase_price = 0
    long_hold = 0
    short_hold = 0
    i = 0

    def init(self):
        super().init()

        #  Calculate indicators
        self.range_filter = self.I(vumanchu_swing, self.data.df, self.swing_period, self.swing_multiplier)

    def next(self):
        super().init()

        self.i += 1

        long_entry_signals = 0
        long_exit_signals = 0
        short_entry_signals = 0
        short_exit_signals = 0

        #  Check Vuman Chu Range Filter
        if self.range_filter[-1] > self.range_filter[-2]:
            long_entry_signals += 1
            short_exit_signals += 1

        if self.range_filter[-1] < self.range_filter[-2]:
            long_exit_signals += 1
            short_entry_signals += 1

        #  Stop loss
        price = self.data.df['Close'][-1]
        if price <= self.last_purchase_price * (1 - self.stop_loss_percent/100):
            long_exit_signals += 1

        if price >= self.last_purchase_price * (1 + self.stop_loss_percent/100):
            short_exit_signals += 1

        #  LONG
        #--------------------------------------------------
        if self.long_hold == 0 and long_entry_signals >= 1:
            #  Buy
            self.long_hold = 1
            self.position.close()
            self.buy()
            self.last_purchase_price = price

        elif self.long_hold == 1 and long_exit_signals >= 1:
            # Close any existing long trades, and sell the asset
            self.long_hold = 0
            self.position.close()
            self.last_purchase_price = 0

        #  SHORT
        #--------------------------------------------------
        if self.short_hold == 0 and short_entry_signals >= 1:
            #  Sell
            self.short_hold = 1
            self.position.close()
            self.sell()
            self.last_purchase_price = price

        elif self.short_hold == 1 and short_exit_signals >= 1:
            # Close any existing long trades, and sell the asset
            self.short_hold = 0
            self.position.close()
            self.last_purchase_price = 0

def load_data_file(symbol, interval):

    file_path = os.path.join(DATA_PATH, f"{symbol}_{interval}_ohlc.csv")
    if not exists(file_path):
        print(f"Error loading file {file_path}")
        return None

    #  Load data file
    df = pd.read_csv(file_path)
    if df is None or len(df) == 0:
        print(f"Empty file: {file_path}")
        return None

    #  Shorten df for testing
    #df = df.iloc[30000:40000]

    #  Rename columns
    df = df.rename(columns={"open": "Open", "close": "Close", "low": "Low", "high": "High", "volume": "Volume"})

    df['Date'] = pd.to_datetime(df['unix'], unit='s', utc=True)
    df = df.drop(['unix'], axis=1)
    df = df.set_index('Date')

    #  Drop na
    df.dropna(axis=0, how='any', inplace=True)

    return df


def run_backtest(df):
    # If exclusive orders (each new order auto-closes previous orders/position),
    # cancel all non-contingent orders and close all open trades beforehand
    bt = Backtest(df, MixedStrategy, cash=1000, commission=.00075, trade_on_close=True, exclusive_orders=False, hedging=False)
    stats = bt.run()
    print(stats)
    bt.plot()

symbols = ['BTC-USD', 'ETH-USD', 'LTC-USD', 'ALGO-USD','XLM-USD','BAT-USD']

# MAIN
if __name__ == '__main__':
    symbol = 'LTC-USD'
    df = load_data_file(symbol, '5m')

    #  Run backtest
    run_backtest(df)
