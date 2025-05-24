import yfinance as yf
import pandas as pd
from tqdm import tqdm
import requests
import json
import time

FINNHUB_API_KEY = "d0nmpqpr01qn5ghknpv0d0nmpqpr01qn5ghknpvg"

def enrich_with_finnhub(symbol):
    """Fetch company details from Finnhub API"""
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        time.sleep(1)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        data = response.json()

        # Extract relevant fields
        return {
            "Symbol": symbol,
            "Name": data.get("name"),
            "CEO": data.get("ceo"),
            "MarketCap": data.get("marketCapitalization"),
            "Employees": data.get("employeeTotal"),
            "Headquarters": data.get("hq_country"),
            "Industry": data.get("finnhubIndustry"),
        }
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to fetch data for {symbol}: {e}")
        return None

def get_stock_symbols():
    """Fetch US-listed stock symbols from Nasdaq API"""
    url = "https://api.nasdaq.com/api/screener/stocks?download=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    # Parse the JSON response
    try:
        data = response.json()  # Parse JSON
        rows = data.get("data", {}).get("rows", [])  # Safely navigate the JSON structure

        # Extract symbols and names
        symbols = [
            {"symbol": r.get("symbol"), "name": r.get("name")}
            for r in rows
            if r.get("symbol") and r.get("name")  # Ensure both 'symbol' and 'name' exist
        ]
        return symbols

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []
    except KeyError as e:
        print(f"Missing key in JSON response: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def extract_ceo_name(info):
    """Try to extract CEO name from yfinance metadata"""
    officers = info.get("companyOfficers", [])
    for officer in officers:
        if officer.get("title", "").lower().startswith("ceo"):
            return officer.get("name")
    return None

def enrich_with_yfinance(symbol):
    """Gather metadata from yfinance and classify CEO"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        ceo_name = extract_ceo_name(info)

        return {
            "Symbol": symbol,
            "Name": info.get("shortName"),
            "CEO": ceo_name,
            "MarketCap": info.get("marketCap"),
            "Employees": info.get("fullTimeEmployees"),
            "Headquarters": f"{info.get('city', '')}, {info.get('state', '')}",
            "Founded": info.get("longBusinessSummary", "")[:10],  # crude fallback
            "Exchange": info.get("exchange"),
            "Industry": info.get("industry"),
        }
    except Exception as e:
        print(f"[Error] {symbol}: {e}")
        return None

def main():
    print("📥 Fetching stock symbols...")
    symbols = get_stock_symbols()

    print(f"🔍 Enriching {len(symbols)} companies with metadata...")
    enriched_data = []

    for entry in tqdm(symbols[:100]):  # Adjust/remove slice to process more
        #data = enrich_with_yfinance(entry["symbol"])
        data = enrich_with_finnhub(entry["symbol"])
        if data:
            enriched_data.append(data)

    # Save enriched data to a CSV file
    df = pd.DataFrame(enriched_data)
    df.to_csv("enriched_stock_data.csv", index=False)
    print("✅ Data saved to enriched_stock_data.csv")

if __name__ == "__main__":
    main()