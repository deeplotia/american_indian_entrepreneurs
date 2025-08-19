"""
Main execution script for the American Indian Entrepreneurs project.

This script demonstrates the refactored, object-oriented approach to fetching
company details from various financial websites using modern Python best practices.
"""

import datetime
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from tqdm import tqdm

from src.fetch_company_details import CompanyDetails, CompanyDetailsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NasdaqDataProcessor:
    """Handles fetching and processing of Nasdaq stock screener data."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def get_stock_screener_data(self) -> pd.DataFrame:
        """Fetch stock screener data from Nasdaq API."""
        url = "https://api.nasdaq.com/api/screener/stocks?download=true"
        logger.info("Fetching data from Nasdaq's stock screener")

        try:
            import requests

            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from Nasdaq's stock screener")
            return pd.DataFrame(data["data"]["rows"])
        except Exception as e:
            logger.error(f"Failed to fetch data from Nasdaq: {e}")
            raise


class DataProcessor:
    """Main data processing class with improved threading and error handling."""

    def __init__(self, max_workers: int = None, batch_size: int = 50):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.batch_size = batch_size
        self.fetcher = CompanyDetailsFetcher(max_workers=self.max_workers)
        self.nasdaq_processor = NasdaqDataProcessor()

    def process_stock_data(self, limit: int = None) -> pd.DataFrame:
        """Process stock data and enrich with company details."""
        # Fetch stock data
        df = self.nasdaq_processor.get_stock_screener_data()

        if limit:
            df = df.head(limit)

        # Add new columns for company details
        df = self._add_company_detail_columns(df)

        # Process companies in batches
        df = self._process_companies_batch(df)

        return df

    def _add_company_detail_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add columns for company details."""
        new_columns = {
            "CEO": "",
            "Employees": "",
            "Headquarters": "",
            "Founded": "",
            "Industry": "",
            "Source": "",
            "Source Link": "",
        }

        for col_name, default_value in new_columns.items():
            if col_name not in df.columns:
                df[col_name] = default_value

        return df

    def _process_companies_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process companies in batches using ThreadPoolExecutor."""
        total_rows = len(df)
        logger.info(
            f"Processing {total_rows} companies with {self.max_workers} workers"
        )

        start_time = time.time()
        processed_count = 0

        # Process in batches
        for batch_start in tqdm(
            range(0, total_rows, self.batch_size), desc="Processing batches"
        ):
            batch_end = min(batch_start + self.batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end].copy()

            # Extract tickers for this batch
            tickers = batch_df["symbol"].tolist()

            # Fetch company details for this batch
            company_details = self.fetcher.fetch_multiple_companies(tickers)

            # Update DataFrame with fetched details
            for i, ticker in enumerate(tickers):
                row_index = batch_start + i
                if ticker in company_details:
                    details = company_details[ticker]
                    self._update_dataframe_row(df, row_index, details)
                    processed_count += 1

            # Log progress
            if processed_count % 10 == 0:
                elapsed_time = time.time() - start_time
                estimated_total = (
                    (elapsed_time / processed_count) * total_rows
                    if processed_count > 0
                    else 0
                )
                remaining_time = estimated_total - elapsed_time

                logger.info(
                    f"Processed {processed_count}/{total_rows} companies. "
                    f"Elapsed: {self._format_time(elapsed_time)}, "
                    f"Remaining: {self._format_time(remaining_time)}"
                )

        logger.info(f"Completed processing {total_rows} companies")
        return df

    def _update_dataframe_row(
        self, df: pd.DataFrame, row_index: int, details: CompanyDetails
    ):
        """Update a DataFrame row with company details."""
        details_dict = details.to_dict()

        df.at[row_index, "CEO"] = details_dict["ceo"]
        df.at[row_index, "Employees"] = details_dict["employees"]
        df.at[row_index, "Headquarters"] = details_dict["headquarters"]
        df.at[row_index, "Founded"] = details_dict["founded"]
        df.at[row_index, "Industry"] = details_dict["industry"]
        df.at[row_index, "Source"] = details_dict["sources"]
        df.at[row_index, "Source Link"] = details_dict["urls"]

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to human-readable format."""
        return time.strftime("%Hh:%Mm:%Ss", time.gmtime(seconds))


class DataExporter:
    """Handles exporting processed data to various formats."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """Export DataFrame to CSV format."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nasdaq_screener_{timestamp}.csv"

        filepath = self.output_dir / filename

        # Define columns to export
        export_columns = [
            "symbol",
            "name",
            "marketCap",
            "CEO",
            "Employees",
            "Headquarters",
            "Founded",
            "Industry",
            "Source",
            "Source Link",
        ]

        # Rename columns for export
        column_mapping = {
            "symbol": "Symbol",
            "name": "Name",
            "marketCap": "Market Capital",
            "CEO": "CEO",
            "Employees": "Employees",
            "Headquarters": "Headquarters",
            "Founded": "Founded",
            "Industry": "Industry",
            "Source": "Source",
            "Source Link": "Source Link",
        }

        export_df = df[export_columns].copy()
        export_df.columns = [column_mapping[col] for col in export_columns]

        export_df.to_csv(filepath, index=False)
        logger.info(f"Data exported to CSV: {filepath}")
        return str(filepath)

    def export_to_excel(self, df: pd.DataFrame, filename: str = None) -> str:
        """Export DataFrame to Excel format."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nasdaq_screener_{timestamp}.xlsx"

        filepath = self.output_dir / filename

        # Define columns to export
        export_columns = [
            "symbol",
            "name",
            "marketCap",
            "CEO",
            "Employees",
            "Headquarters",
            "Founded",
            "Industry",
            "Source",
            "Source Link",
        ]

        # Rename columns for export
        column_mapping = {
            "symbol": "Symbol",
            "name": "Name",
            "marketCap": "Market Capital",
            "CEO": "CEO",
            "Employees": "Employees",
            "Headquarters": "Headquarters",
            "Founded": "Founded",
            "Industry": "Industry",
            "Source": "Source",
            "Source Link": "Source Link",
        }

        export_df = df[export_columns].copy()
        export_df.columns = [column_mapping[col] for col in export_columns]

        export_df.to_excel(filepath, index=False)
        logger.info(f"Data exported to Excel: {filepath}")
        return str(filepath)


def main():
    """Main execution function."""
    try:
        # Initialize processors
        processor = DataProcessor(max_workers=8, batch_size=25)  # Conservative settings
        exporter = DataExporter()

        # Process stock data (limit to first 100 for testing)
        logger.info("Starting stock data processing...")
        df = processor.process_stock_data(limit=None)  # Remove limit for full processing

        # Export a single CSV result
        csv_file = exporter.export_to_csv(df)

        logger.info("Processing completed successfully!")
        logger.info(f"Results saved to: {csv_file}")

        # Print summary
        total_companies = len(df)
        companies_with_ceo = len(df[df["CEO"].notna() & (df["CEO"] != "")])
        companies_with_employees = len(
            df[df["Employees"].notna() & (df["Employees"] != "")]
        )
        companies_with_headquarters = len(
            df[df["Headquarters"].notna() & (df["Headquarters"] != "")]
        )

        logger.info(f"Summary:")
        logger.info(f"  Total companies processed: {total_companies}")
        logger.info(
            f"  Companies with CEO info: {companies_with_ceo} ({companies_with_ceo/total_companies*100:.1f}%)"
        )
        logger.info(
            f"  Companies with employee count: {companies_with_employees} ({companies_with_employees/total_companies*100:.1f}%)"
        )
        logger.info(
            f"  Companies with headquarters: {companies_with_headquarters} ({companies_with_headquarters/total_companies*100:.1f}%)"
        )

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
        raise


if __name__ == "__main__":
    main()
