import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

from src.http.http_client import HTTPClient
from src.models.company_details import CompanyDetails
from src.scrapers.base import BaseScraper
from src.scrapers.cnbc import CNBCScraper
from src.scrapers.cnn_money import CNNScraper
from src.scrapers.google_finance import GoogleFinanceScraper
from src.scrapers.marketwatch import MarketWatchScraper
from src.scrapers.yahoo_finance import YahooFinanceScraper


logger = logging.getLogger(__name__)


class CompanyDetailsFetcher:
    """Main class for fetching company details from multiple sources."""

    def __init__(self, max_workers: int | None = None):
        self.http_client = HTTPClient()
        self.scrapers: list[BaseScraper] = [
            GoogleFinanceScraper(self.http_client),
            CNBCScraper(self.http_client),
            MarketWatchScraper(self.http_client),
            YahooFinanceScraper(self.http_client),
            # CNNScraper(self.http_client),  # optional
        ]
        self.max_workers = max_workers or min(4, (os.cpu_count() or 1))
        self.rate_limit_count = 0
        self.last_rate_limit_time = 0

    def fetch_company_details(self, ticker: str) -> CompanyDetails:
        company_details = CompanyDetails()
        ticker = self._clean_ticker(ticker)

        logger.info(f"Fetching details for ticker: {ticker}")

        current_time = time.time()
        if self.rate_limit_count > 3 and current_time - self.last_rate_limit_time < 300:
            logger.warning("Rate limit cooldown active, skipping request")
            return company_details

        for scraper in self.scrapers:
            try:
                company_details = scraper.scrape(ticker, company_details)
                if company_details.is_complete():
                    logger.info(
                        f"Complete data found for {ticker} from {scraper.__class__.__name__}"
                    )
                    break
            except Exception as error:
                logger.error(
                    f"Error scraping {ticker} with {scraper.__class__.__name__}: {error}"
                )
                if "429" in str(error) or "rate limit" in str(error).lower():
                    self.rate_limit_count += 1
                    self.last_rate_limit_time = current_time
                continue

        return company_details

    def fetch_multiple_companies(self, tickers: list[str]) -> Dict[str, CompanyDetails]:
        results: Dict[str, CompanyDetails] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(self.fetch_company_details, ticker): ticker
                for ticker in tickers
            }
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    results[ticker] = future.result()
                    time.sleep(0.5)
                except Exception as error:
                    logger.error(f"Error processing {ticker}: {error}")
                    results[ticker] = CompanyDetails()
        return results

    def _clean_ticker(self, ticker: str) -> str:
        ticker = ticker.replace("^", "").replace("/", "")
        return ticker.strip()


