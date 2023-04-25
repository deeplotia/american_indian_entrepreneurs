import datetime
import json
from threading import Thread

import pandas as pd

from fetch_company_details import *


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
df.insert(13, "Employees", "")
df.insert(14, "Headquarters", "")
df.insert(15, "Founded", "")
df.insert(16, "Industry", "")
df.insert(17, "Source", "")
df.insert(18, "Source Link", "")

total_rows = len(df)

rows_per_thread = 25
total_threads = (total_rows / rows_per_thread).__ceil__()
print("Total Rows: {} and Total Threads: {}".format(total_rows, total_threads))
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


def set_ceo_details_new(index, company_details: dict, ticker):
    df.iloc[index, 12] = company_details.get("ceo", "")
    df.iloc[index, 13] = company_details.get("employees", "")
    df.iloc[index, 14] = company_details.get("headquarters", "")
    df.iloc[index, 15] = company_details.get("founded", "")
    df.iloc[index, 16] = company_details.get("industry", "")
    df.iloc[index, 17] = ','.join(company_details.get("source")) if company_details.get("source") else ""
    df.iloc[index, 18] = ','.join(company_details.get("url")) if company_details.get("url") else ""
    print("#{}: ".format(index + 1),
          "Ticker:{}, ".format(ticker),
          "CEO:{}, ".format(company_details.get("ceo")),
          "Employees:{}, ".format(company_details.get("employees")),
          "Headquarters:{}, ".format(company_details.get("headquarters")),
          "Founded:{}, ".format(company_details.get("founded")),
          "Industry:{}, ".format(company_details.get("industry")),
          "Source:{}, ".format(','.join(company_details.get("source")) if company_details.get("source") else ""),
          sep="")


# initialize dictionary to populate company details
def initialize_company_details_dict():
    # todo: set a separate dict for source info

    return {
        "source": set(),
        "url": set(),
        "ceo": None,
        "employees": None,
        "headquarters": None,
        "founded": None,
        "industry": None
    }


# Start Fetching Operation
def fetch(num: int):
    start_row = num * rows_per_thread
    end_row = start_row + rows_per_thread
    if end_row >= total_rows:
        end_row = total_rows
    for row_index in range(start_row, end_row):
        company_details: dict = initialize_company_details_dict()
        ticker: str = df.iloc[row_index, 0]

        ind = ticker.rfind("^")
        if ind != -1:
            ticker = ticker[:ind]

        ind = ticker.rfind("/")
        if ind != -1:
            ticker = ticker[:ind]

        ticker = ticker.strip()
        company_details = get_from_gfinance_nasdaq(ticker, company_details)
        if None in company_details.values():
            company_details = get_from_gfinance_nyse(ticker, company_details)
        if None in company_details.values():
            company_details = get_from_cnbc(ticker, company_details)
        if None in company_details.values():
            company_details = get_from_cnn(ticker, company_details)
        if None in company_details.values():
            company_details = get_from_market_watch(ticker, company_details)
        if None in company_details.values():
            company_details = get_from_yahoo_finance(ticker, company_details)
        set_ceo_details_new(row_index, company_details, ticker)

        global row_cnt
        row_cnt += 1
        if row_cnt % 10 == 0:
            estimation = calc_process_time(start_time, row_cnt, total_rows)
            print("time elapsed: %s, estimated time left: %s, estimated finish time: %s"
                  % estimation)

    else:
        global cnt
        cnt += 1
        print("Thread finished: {} out of {}".format(cnt, total_threads))
        if cnt >= total_threads - 1:
            write_to_excel()
        else:
            print("Count {} and Total Threads {}".format(cnt, total_threads))


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
    df.to_excel(name, index=False,
                columns=["symbol", "name", "marketCap", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                         "Source",
                         "Source Link"],
                header=["Symbol", "Name", "Market Capital", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                        "Source",
                        "Source Link"])
    print("{} generated successfully".format(name))


for thread_index in range(total_threads):
    print("starting thread " + str(thread_index + 1))
    t = Thread(target=fetch, args=(thread_index,))
    t.start()
