# Phase 1: Fetch Stock Data and CEO Metadata (Mock Example Using CSV)

import csv
import requests
import pandas as pd
import asyncio
import httpx

# For demonstration: using a local CSV instead of live API for stock metadata
# In production, use IEX Cloud, Nasdaq Screener, etc.
stock_data = [
    {"symbol": "AAPL", "name": "Apple Inc.", "CEO": "Tim Cook", "marketCap": "2.7T", "employees": 164000, "headquarters": "Cupertino, CA", "industry": "Consumer Electronics", "founded": 1976},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "CEO": "Satya Nadella", "marketCap": "2.5T", "employees": 221000, "headquarters": "Redmond, WA", "industry": "Software", "founded": 1975},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "CEO": "Sundar Pichai", "marketCap": "1.8T", "employees": 180000, "headquarters": "Mountain View, CA", "industry": "Internet", "founded": 1998},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "CEO": "Andy Jassy", "marketCap": "1.5T", "employees": 1608000, "headquarters": "Seattle, WA", "industry": "E-Commerce", "founded": 1994},
]

# Save to CSV
with open("stocks_metadata.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=stock_data[0].keys())
    writer.writeheader()
    writer.writerows(stock_data)

print("Stock metadata saved to stocks_metadata.csv")

# Phase 2: Determine Indian-Origin CEOs using Ollama Serve

def clean_response(resp_text):
    resp_text = resp_text.strip().lower()
    return "yes" if "yes" in resp_text else "no"

async def query_ollama(name):
    prompt = f'Is the name "{name}" of Indian origin? Answer Yes or No.'
    payload = {"model": "deepseek:latest", "prompt": prompt, "stream": False}
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:11434/api/generate", json=payload)
        result = response.json().get("response", "")
        return clean_response(result)

async def batch_check_ceos(df):
    unique_names = df["CEO"].dropna().unique()
    tasks = [query_ollama(name) for name in unique_names]
    results = await asyncio.gather(*tasks)
    return dict(zip(unique_names, results))

# Load CSV
df = pd.read_csv("stocks_metadata.csv")
results = asyncio.run(batch_check_ceos(df))
df["ceo_origin"] = df["CEO"].map(results)
df.to_csv("ceo_with_origin.csv", index=False)
print("Saved CEO origin results to ceo_with_origin.csv")




