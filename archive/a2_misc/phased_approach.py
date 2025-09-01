# Phase 1: Fetch Stock Data and CEO Metadata (Mock Example Using CSV)

import csv
import requests
import pandas as pd
import asyncio
import httpx

# For demonstration: using a local CSV instead of live API for stock metadata
# In production, use IEX Cloud, Nasdaq Screener, etc.

# Phase 2: Determine Indian-Origin CEOs using Ollama Serve

def clean_response(resp_text):
    resp_text = resp_text.strip().lower()
    if "yes" in resp_text:
        return "yes"
    elif "no" in resp_text:
        return "no"
    else:
        return "unsure"

async def query_ollama(name):
    prompt = f'Is the name "{name}" of Indian origin? Answer Yes, No or Ambiguous. One word answer no punctuation.'
    payload = {"model": "qwen3:8b", "prompt": prompt, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # 30 second timeout
            response = await client.post("http://localhost:11434/api/generate", json=payload)
            if response.status_code == 404:
                raise Exception("Ollama API endpoint not found. Make sure Ollama is running and the model is installed.")
            response.raise_for_status()
            result = response.json().get("response", "")
            if not result:
                raise Exception("Empty response from Ollama")
            return clean_response(result)
    except httpx.TimeoutException:
        print(f"Timeout while querying Ollama for name {name}")
        return "no"
    except httpx.RequestError as e:
        print(f"Connection error for name {name}: {str(e)}")
        return "no"
    except Exception as e:
        print(f"Error querying Ollama for name {name}: {str(e)}")
        return "no"  # Default to "no" in case of error

async def batch_check_ceos(df):
    unique_names = df["CEO"].dropna().unique()
    # Process in smaller batches to avoid overwhelming the server
    batch_size = 5
    all_results = {}
    
    for i in range(0, len(unique_names), batch_size):
        batch = unique_names[i:i + batch_size]
        tasks = [query_ollama(name) for name in batch]
        results = await asyncio.gather(*tasks)
        all_results.update(dict(zip(batch, results)))
        # Add a small delay between batches
        await asyncio.sleep(1)
    
    return all_results

# Load CSV
df = pd.read_csv("PublicCompaniesMay2025.csv")
results = asyncio.run(batch_check_ceos(df))
df["ceo_indian_origin"] = df["CEO"].map(results)
df.to_csv("ceo_with_indian_origin.csv", index=False)
print("Saved CEO origin results to ceo_with_origin.csv")




