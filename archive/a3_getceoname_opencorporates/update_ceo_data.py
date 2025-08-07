import csv
import requests
from bs4 import BeautifulSoup
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_ceo_from_opencorporates(symbol, api_key=None):
    """Fetch CEO name from OpenCorporates API."""
    logger.info(f"Attempting to fetch CEO data from OpenCorporates for symbol: {symbol}")
    api_url = f"https://api.opencorporates.com/v0.4/companies/search?q={symbol}"
    if api_key:
        api_url += f"&api_token={api_key}"
    
    time.sleep(1)  # Sleep for 1 second to respect rate limit
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if data.get("results", {}).get("companies"):
                ceo_name = data["results"]["companies"][0].get("company", {}).get("officers", [{}])[0].get("name")
                if ceo_name:
                    logger.info(f"Successfully found CEO {ceo_name} from OpenCorporates for {symbol}")
                    return ceo_name
                else:
                    logger.warning(f"No CEO found in OpenCorporates data for {symbol}")
            else:
                logger.warning(f"No company data found in OpenCorporates for {symbol}")
        else:
            logger.error(f"OpenCorporates API request failed with status code {response.status_code} for {symbol}")
    except Exception as e:
        logger.error(f"Error fetching from OpenCorporates for {symbol}: {str(e)}")
    return None

def fetch_ceo_from_wikipedia(company_name):
    """Fetch CEO name from Wikipedia."""
    logger.info(f"Attempting to fetch CEO data from Wikipedia for company: {company_name}")
    search_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            infobox = soup.find("table", {"class": "infobox"})
            if infobox:
                for row in infobox.find_all("tr"):
                    if "CEO" in row.text:
                        ceo_name = row.find("td").text.strip()
                        logger.info(f"Successfully found CEO {ceo_name} from Wikipedia for {company_name}")
                        return ceo_name
            logger.warning(f"No CEO information found in Wikipedia infobox for {company_name}")
        else:
            logger.error(f"Wikipedia request failed with status code {response.status_code} for {company_name}")
    except Exception as e:
        logger.error(f"Error fetching from Wikipedia for {company_name}: {str(e)}")
    return None

# (Removed get_rows_with_empty_ceo as it was redundant and only used for logging)
def update_csv(input_file_path, output_file_path, api_key=None):
    """Update the CSV file with fetched CEO data."""
    logger.info(f"Starting CSV update process for file: {input_file_path}")
    updated_rows = []
    total_rows = 0
    updated_count = 0

    try:
        with open(input_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            # Ensure 'CEO' is a fieldname, or add it if it's missing
            if 'CEO' not in fieldnames:
                fieldnames.append('CEO')

            for row in reader:
                total_rows += 1
                # Use .get() to avoid KeyError if 'CEO' column doesn't exist in some rows
                if not row.get("CEO"):
                    logger.info(f"Processing row {total_rows}: {row.get('Name')} ({row.get('Symbol')})")
                    ceo_name = fetch_ceo_from_opencorporates(row.get("Symbol"), api_key)
                    if ceo_name:
                        row["CEO"] = ceo_name
                        updated_count += 1
                    else:
                        row["CEO"] = "Unknown"
                        logger.warning(f"Could not find CEO for {row.get('Name')} ({row.get('Symbol')})")
                updated_rows.append(row)

        # Write updated rows to the new CSV file
        with open(output_file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)

        logger.info(f"CSV update completed. Processed {total_rows} rows, updated {updated_count} CEO entries.")
    except FileNotFoundError:
        logger.error(f"Error: The file '{input_file_path}' was not found.")
        raise
    except Exception as e:
        logger.error(f"An error occurred while processing the CSV file: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting CEO data update script")
    api_key = '48CoB0SMG4aX79rbdhlw'#os.getenv("OPEN_CORPORATES_API_KEY")
    if not api_key:
        logger.warning("OPEN_CORPORATES_API_KEY environment variable not set. Making unauthenticated requests.")
    
    input_csv_path = "/Users/deeplotia/workspace/personal/american_indian_entrepreneurs/archive/a3_getceoname_opencorporates/PublicCompaniesMay2025_main.csv"
    # Create a new filename for the output
    base, ext = os.path.splitext(input_csv_path)
    output_csv_path = f"{base}_updated{ext}"

    update_csv(input_csv_path, output_csv_path, api_key)
    logger.info(f"Script completed successfully. Updated file saved to {output_csv_path}")