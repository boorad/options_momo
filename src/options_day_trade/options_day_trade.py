import yfinance as yf
from math import ceil, trunc
import pandas as pd
import pendulum
from polygon_client import client
from backtesting import Strategy
import pandas_market_calendars as mcal

nyse = mcal.get_calendar("NYSE")


def get_open(symbol, d):
    ticker = yf.Ticker(symbol)
    history = ticker.history(start=d, period="1d", interval="1d")
    if history.empty:
        if d == pendulum.today():
            return ticker.info["open"]
        else:
            return None
    else:
        return history.iloc[0]["Open"]


def get_eow(trade_day):
    d = pendulum.instance(trade_day)
    sow = pd.Timestamp(ts_input=d.start_of("week")).tz_convert(nyse.tz.zone)
    eow = pd.Timestamp(ts_input=d.end_of("week")).tz_convert(nyse.tz.zone)
    trading_days = nyse.valid_days(start_date=sow, end_date=eow, tz=nyse.tz.zone)
    return trading_days[-1].strftime("%Y-%m-%d")


def get_contract(symbol, type, target, expiry, as_of):
    contracts = client.list_options_contracts(
        underlying_ticker=symbol,
        contract_type=type,
        expiration_date=expiry,
        strike_price=target,
        as_of=as_of,
    )
    return next(contracts, None)


def OptionsDayTrade(Strategy):
    def init(self):
        pass

    def next(self):
        pass


def main():
    symbol = "SPY"
    today = pendulum.today()
    open = get_open(symbol, today)
    expiry = get_eow(today)
    call = get_contract(symbol, "call", trunc(open), expiry, today)
    put = get_contract(symbol, "put", ceil(open), expiry, today)

    print(f"symbol : {symbol}")
    print(f"today  : {today}")
    print(f"open   : {open}")
    print(f"expiry : {expiry}")
    print(f"call   : {call}")
    print(f"put    : {put}")


if __name__ == "__main__":
    main()
