import pandas as pd
from openai import OpenAI

# DeepSeek API configuration
DEEPSEEK_API_KEY = "sk-19436520b77848459cb207077fcbc700"  # Replace with your actual API key
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Initialize the DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def fetch_ceo_from_deepseek(symbol, company_name, headquarters):
    """Fetch CEO name using DeepSeek's chat model."""
    try:
        # Construct the chat messages
        # Extract headquarters information from the CSV row

        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides CEO (Chief Executive Officer) names for companies that are listed in NASDAQ. Just provide the CEO Full Name nothing else."},
            {"role": "user", "content": f"Find the CEO of the company with symbol '{symbol}', name '{company_name}', and headquartered in '{headquarters}' to be precise."}
        ]

        # Call the DeepSeek chat model
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )

        # Extract the CEO name from the response
        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            print(f"[Error] No valid response for {symbol} ({company_name}).")
    except Exception as e:
        print(f"[Error] Failed to fetch CEO for {symbol} ({company_name}): {e}")
    return None

def update_ceo_in_csv(file_path):
    """Read the CSV, fetch missing CEO names, and update the file."""
    # Read the CSV into a Pandas DataFrame
    df = pd.read_csv(file_path, sep=";")

    # Filter rows where the CEO column is empty
    missing_ceo_rows = df[df["CEO"].isna()]

    print(f"Found {len(missing_ceo_rows)} rows with missing CEO information.")

    # Iterate over rows with missing CEO values
    for index, row in missing_ceo_rows.iterrows():
        print(f"Fetching CEO for {row['Symbol']} ({row['Name']})...")
        ceo_name = fetch_ceo_from_deepseek(row["Symbol"], row["Name"], row["Headquarters"])
        df.at[index, "CEO"] = ceo_name if ceo_name else "Unknown"  # Update the CEO column
        print(f"Company Name: {row['Name']}, Ticker: {row['Symbol']}, CEO name: {ceo_name}")

    # Save the updated DataFrame back to the CSV file
    df.to_csv(file_path, index=False)
    print("CSV file updated successfully.")

# Run the script
update_ceo_in_csv("/Users/deeplotia/workspace/personal/american_indian_entrepreneurs/archive/PublicCompaniesMay2025.csv")