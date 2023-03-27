import csv
import os
import pandas as pd
import pendulum
from math import ceil, trunc
from polygon_client import client
from polygon.exceptions import NoResultsError
from options_day_trade import get_open, get_eow, get_contract
import pandas_market_calendars as mcal

nyse = mcal.get_calendar("NYSE")


def main(symbol):
    print(symbol)
    # first day of options quote data in polygon
    start = (
        pd.Timestamp(ts_input=pendulum.datetime(2022, 3, 7, 12))
        .tz_convert(nyse.tz.zone)
        .normalize()
    )
    today = pd.Timestamp(ts_input=pendulum.today()).tz_convert(nyse.tz.zone).normalize()
    trading_days = nyse.valid_days(start_date=start, end_date=today, tz=nyse.tz.zone)
    for d in trading_days:
        get_data(symbol, pd.to_datetime(d))


def get_data(symbol, d):
    open = get_open(symbol, d)
    expiry = get_eow(d)
    day = d.strftime("%Y-%m-%d")

    call = get_contract(symbol, "call", trunc(open), expiry, day)
    if call:
        try:
            call_data = []
            for q in client.list_quotes(
                call.ticker, timestamp=day, limit=50000, sort="timestamp", order="asc"
            ):
                call_data.append(q)
            print(f"{day}\t{open}\t{expiry}\t{call.strike_price}C\t{len(call_data)}")
            ohlcs = tick_to_ohlc(call_data)
            write_data(symbol, "call", ohlcs)
        except NoResultsError:
            print(f"{day}\t{open}\t{expiry}\tno call data")
    else:
        print(f"{day}\t{open}\t{expiry}\tno call data")

    put = get_contract(symbol, "put", ceil(open), expiry, day)
    if put:
        try:
            put_data = []
            for q in client.list_quotes(
                put.ticker, timestamp=day, limit=50000, sort="timestamp", order="asc"
            ):
                put_data.append(q)
            print(f"{day}\t{open}\t{expiry}\t{put.strike_price}P\t{len(put_data)}")
            ohlcs = tick_to_ohlc(put_data)
            write_data(symbol, "put", ohlcs)
        except NoResultsError:
            print(f"{day}\t{open}\t{expiry}\tno put data")
    else:
        print(f"{day}\t{open}\t{expiry}\tno put data")


def tick_to_ohlc(data):
    ohlcs = []
    buckets = {}
    # fill one-second buckets
    for tick in data:
        seconds, nanos = divmod(tick.sip_timestamp, 1000 * 1000 * 1000)  # ns -> sec
        if not buckets.get(seconds):
            buckets[seconds] = []
        buckets[seconds].append((nanos, tick.bid_price))

    # sort and process buckets
    keys = sorted(buckets.keys())
    for bucket_key in keys:
        ohlc = {}
        ohlc["ts"] = bucket_key
        bucket = buckets[bucket_key]
        bucket.sort()
        ohlc["Open"] = bucket[0][1]
        ohlc["Close"] = bucket[-1][1]
        prices = [p[1] for p in bucket]
        ohlc["High"] = max(prices)
        ohlc["Low"] = min(prices)
        ohlcs.append(ohlc)
    return ohlcs


def write_data(symbol, option, data):
    filename = f"data/{symbol}-{option}.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as csvfile:
        field_names = ["ts", "Open", "High", "Low", "Close"]
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)


if __name__ == "__main__":
    symbol = "SPY"
    main(symbol)
