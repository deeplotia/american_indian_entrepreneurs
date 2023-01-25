import datetime
import json
from threading import Thread

import pandas as pd

from ceo_fetch import *


# Get Stock Screener Data From Nasdaq
def get_stock_screener_data():
    url = "https://api.nasdaq.com/api/screener/stocks?download=true"
    print("fetching data from nasdaq's stock screener")
    res = requests.get(url, headers=headers)
    data = json.loads(res.content)
    print("data fetched from nasdaq's stock screener")
    return pd.DataFrame(data['data']['rows'])


df = get_stock_screener_data()
df.insert(12, "CEO", "")
df.insert(13, "Source", "")
df.insert(14, "Source Link", "")

total_rows = len(df)

rows_per_thread = 100
total_threads = (total_rows / rows_per_thread).__ceil__()
cnt = 0
row_cnt = 0
start_time = time.time()


# Save Ceo Details to the DataFrame
def set_ceo_details(index, ceo, source, url, ticker):
    df.iloc[index, 12] = ceo
    df.iloc[index, 13] = source
    df.iloc[index, 14] = url
    print("#{}: ".format(index + 1), "Ticker:{}, ".format(ticker), "CEO:{}, ".format(ceo), "Source:{}".format(source),
          sep="")


# Start Fetching Operation
def fetch(num: int):
    start_row = num * rows_per_thread
    end_row = start_row + rows_per_thread
    if end_row >= total_rows:
        end_row = total_rows
    for row_index in range(start_row, end_row):
        ticker: str = df.iloc[row_index, 0]

        ind = ticker.rfind("^")
        if ind != -1:
            ticker = ticker[:ind]

        ind = ticker.rfind("/")
        if ind != -1:
            ticker = ticker[:ind]

        ticker = ticker.strip()
        ceo, source, url = get_from_gfinance_nasdaq(ticker)
        if ceo:
            set_ceo_details(row_index, ceo, source, url, ticker)
        if df.iloc[row_index, 12] == "":
            ceo, source, url = get_from_gfinance_nyse(ticker)
            if ceo:
                set_ceo_details(row_index, ceo, source, url, ticker)
        if df.iloc[row_index, 12] == "":
            ceo, source, url = get_from_cnn(ticker)
            if ceo:
                set_ceo_details(row_index, ceo, source, url, ticker)
        if df.iloc[row_index, 12] == "":
            ceo, source, url = get_from_cnbc(ticker)
            if ceo:
                set_ceo_details(row_index, ceo, source, url, ticker)
        if df.iloc[row_index, 12] == "":
            ceo, source, url = get_from_market_watch(ticker)
            if ceo:
                set_ceo_details(row_index, ceo, source, url, ticker)
        if df.iloc[row_index, 12] == "":
            ceo, source, url = get_from_yahoo_finance(ticker)
            if ceo:
                set_ceo_details(row_index, ceo, source, url, ticker)
            else:
                print("#{}: ".format(row_index + 1), "Ticker:{} ".format(ticker), "(Not Found)", sep="")

        global row_cnt
        row_cnt += 1
        if row_cnt % 10 == 0:
            estimation = calc_process_time(start_time, row_cnt, total_rows)
            print("time elapsed: %s, estimated time left: %s, estimated finish time: %s"
                  % estimation)

    else:
        global cnt
        cnt += 1
        print("Thread finished: {}".format(cnt))
        if cnt == total_threads:
            write_to_excel()

def calc_process_time(started_time, cur_iter, max_iter):
    elapsed = time.time() - started_time
    estimated = (elapsed / cur_iter) * max_iter
    finished = started_time + estimated
    finished = datetime.datetime.fromtimestamp(finished).strftime("%I:%M:%S %p")  # in time
    left = estimated - elapsed  # in seconds

    left = time.strftime('%Hh:%Mm:%Ss', time.gmtime(left))
    elapsed = time.strftime('%Hh:%Mm:%Ss', time.gmtime(elapsed))

    return elapsed, left, finished


# Write data to excel
def write_to_excel():
    name = "nasdaq_screener_{}.xlsx".format(time.time_ns())
    print("writing data to {}".format(name))
    df.to_excel(name, index=False, columns=["symbol", "name", "marketCap", "CEO", "Source", "Source Link"],
                header=["Symbol", "Name", "Market Capital", "CEO", "Source", "Source Link"])
    print("{} generated successfully".format(name))


for thread_index in range(total_threads):
    print("starting thread " + str(thread_index + 1))
    t = Thread(target=fetch, args=(thread_index,))
    t.start()
