
import asyncio
import aiohttp
import datetime
import json
import pandas as pd
from fetch_company_details import *
import time
import traceback
import logging
import os

# LOG configuration START
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(
    LOG_DIR, f"app_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

# file handler (simple single file; rotate later if needed)
fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

# avoid adding duplicate handlers if module reloaded
if not logger.handlers:
    logger.addHandler(ch)
    logger.addHandler(fh)
# LOG configuration END    

# periodic CSV flush configuration
FLUSH_INTERVAL_SECONDS = 30  # flush every N seconds
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _csv_path():
    return os.path.join(OUTPUT_DIR, "nasdaq_screener_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")))

def flush_df_to_csv(path=None):
    """Write current DataFrame snapshot to CSV and fsync to ensure on-disk flush."""
    path = path or _csv_path()
    try:
        # open file and let pandas write into it, then flush+fsync
        with open(path, "w", newline="", encoding="utf-8") as f:
            df.to_csv(f, index=False,
                      columns=["symbol", "name", "marketCap", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                               "Source", "Source Link"],
                      header=["Symbol", "Name", "Market Capital", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                              "Source", "Source Link"])
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # os.fsync may not be available on some platforms or file systems; ignore if it fails
                pass
        logger.info("Flushed DataFrame snapshot to %s", path)
    except Exception as e:
        logger.exception("Failed to flush CSV: %s", e)

async def flush_csv_periodically(done_event: asyncio.Event):
    """Background task that periodically writes current DataFrame to CSV until done_event is set."""
    # use a stable path for interim flushes so file is overwritten rather than creating many files
    interim_path = os.path.join(OUTPUT_DIR, "nasdaq_screener_current.csv")
    while not done_event.is_set():
        await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
        try:
            # write snapshot
            with open(interim_path, "w", newline="", encoding="utf-8") as f:
                df.to_csv(f, index=False,
                          columns=["symbol", "name", "marketCap", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                                   "Source", "Source Link"],
                          header=["Symbol", "Name", "Market Capital", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                                  "Source", "Source Link"])
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            logger.info("Periodic flush wrote snapshot to %s", interim_path)
        except Exception as e:
            logger.exception("Periodic flush failed: %s", e)
    # final flush when stopping
    flush_df_to_csv()

def _filled_count(cd: dict) -> int:
    """Return number of non-empty data fields (excluding source/url sets)."""
    return sum(1 for k, v in cd.items() if k not in ("source", "url") and v)
# ...existing code...

# Get Stock Screener Data From Nasdaq (async, uses aiohttp)
async def async_get_stock_screener_data():
    url = "https://api.nasdaq.com/api/screener/stocks?download=true"
    print("fetching data from nasdaq's stock screener (async)")
    headers_local = headers if 'headers' in globals() else {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers_local) as res:
            raw = await res.read()
            data = json.loads(raw)
    print("data fetched from nasdaq's stock screener")
    return pd.DataFrame(data['data']['rows'])


# synchronous wrapper to keep rest of code shape
def get_stock_screener_data():
    return asyncio.run(async_get_stock_screener_data())

df = get_stock_screener_data()
df.insert(12, "CEO", "")
df.insert(13, "Employees", "")
df.insert(14, "Headquarters", "")
df.insert(15, "Founded", "")
df.insert(16, "Industry", "")
df.insert(17, "Source", "")
df.insert(18, "Source Link", "")

total_rows = len(df)
cnt = 0
row_cnt = 0
start_time = time.time()

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

# Start Fetching Operation (async worker that delegates blocking parsing to threads)
async def _worker(row_index: int, sem: asyncio.Semaphore):
    async with sem:
        try:
            company_details: dict = initialize_company_details_dict()
            ticker: str = df.iloc[row_index, 0]

            logger.info("Start processing row %d/%d: %s", row_index + 1, total_rows, ticker)

            ind = ticker.rfind("^")
            if ind != -1:
                ticker = ticker[:ind]

            ind = ticker.rfind("/")
            if ind != -1:
                ticker = ticker[:ind]

            ticker = ticker.strip()

            logger.debug("Normalized ticker for row %d: %s", row_index + 1, ticker)

           # call your existing blocking functions in a threadpool to avoid blocking the event loop
            logger.info("Fetching %s from gfinance_nasdaq", ticker)
            company_details = await asyncio.to_thread(get_from_gfinance_nasdaq, ticker, company_details)
            logger.info("Finished %s from gfinance_nasdaq; filled=%d", ticker, _filled_count(company_details))
            if None in company_details.values():
                logger.info("Fetching %s from gfinance_nyse", ticker)
                company_details = await asyncio.to_thread(get_from_gfinance_nyse, ticker, company_details)
                logger.info("Finished %s from gfinance_nyse; filled=%d", ticker, _filled_count(company_details))
            if None in company_details.values():
                logger.info("Fetching %s from cnbc", ticker)
                company_details = await asyncio.to_thread(get_from_cnbc, ticker, company_details)
                logger.info("Finished %s from cnbc; filled=%d", ticker, _filled_count(company_details))
            if None in company_details.values():
                logger.info("Fetching %s from cnn", ticker)
                company_details = await asyncio.to_thread(get_from_cnn, ticker, company_details)
                logger.info("Finished %s from cnn; filled=%d", ticker, _filled_count(company_details))
            if None in company_details.values():
                logger.info("Fetching %s from market_watch", ticker)
                company_details = await asyncio.to_thread(get_from_market_watch, ticker, company_details)
                logger.info("Finished %s from market_watch; filled=%d", ticker, _filled_count(company_details))
            if None in company_details.values():
                logger.info("Fetching %s from yahoo_finance", ticker)
                company_details = await asyncio.to_thread(get_from_yahoo_finance, ticker, company_details)
                logger.info("Finished %s from yahoo_finance; filled=%d", ticker, _filled_count(company_details))

           # update dataframe (runs in event loop; small sync operation)
            await asyncio.to_thread(set_ceo_details_new, row_index, company_details, ticker)

            logger.info("Updated DataFrame for %s (row %d). CEO=%s, Employees=%s",
                        ticker, row_index + 1, company_details.get("ceo"), company_details.get("employees"))

            global row_cnt
            row_cnt += 1
            if row_cnt % 10 == 0:
                estimation = calc_process_time(start_time, row_cnt, total_rows)
                print("time elapsed: %s, estimated time left: %s, estimated finish time: %s"
                    % estimation)
        except Exception as e:
            # keep the loop running if one worker fails
            logger.exception("error processing row %d ticker %s: %s", row_index + 1, locals().get("ticker", "<unknown>"), e)
            traceback.print_exc()        

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
def write_to_csv():
    name = "output/nasdaq_screener_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d_%H:%M"))
    print("writing data to {}".format(name))
    df.to_csv(name, index=False,
                columns=["symbol", "name", "marketCap", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                         "Source",
                         "Source Link"],
                header=["Symbol", "Name", "Market Capital", "CEO", "Employees", "Headquarters", "Founded", "Industry",
                        "Source",
                        "Source Link"])
    print("{} generated successfully".format(name))

async def main_async():
    # control concurrent tasks: set concurrency to something reasonable (e.g. 10)
    concurrency = 10
    sem = asyncio.Semaphore(concurrency)

    # start periodic flush background task
    done_event = asyncio.Event()
    flush_task = asyncio.create_task(flush_csv_periodically(done_event))

    tasks = []
    for row_index in range(total_rows):
        tasks.append(asyncio.create_task(_worker(row_index, sem)))

    await asyncio.gather(*tasks)

    # signal flush task to finish and wait
    done_event.set()
    await flush_task

    # when finished write out CSV
    write_to_csv()


# Replace thread-based launch with asyncio run
if __name__ == "__main__":
    # ensure df is populated via async fetch if needed (get_stock_screener_data uses asyncio.run)
    # df already set earlier by calling get_stock_screener_data()
    asyncio.run(main_async())
# ...existing code...