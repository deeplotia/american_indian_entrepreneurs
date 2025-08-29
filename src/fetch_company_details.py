"""Deprecated: logic moved to dedicated modules under `src/`.

This file remains to preserve backwards compatibility of imports. New code
should import from:

- src.models.company_details.CompanyDetails
- src.http.http_client.HTTPClient
- src.scrapers.*
- src.fetchers.company_details_fetcher.CompanyDetailsFetcher
"""

import logging
import os
import random
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

REQUEST_TIMEOUT = 30
MAX_RETRIES = 5
RETRY_DELAY = 2.0
RATE_LIMIT_DELAY = 3.0  # Delay between requests to avoid rate limiting


@dataclass
class CompanyDetails:
    """Data class to store company information."""

    ceo: Optional[str] = None
    employees: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None
    sources: Set[str] = field(default_factory=set)
    urls: Set[str] = field(default_factory=set)

    def is_complete(self) -> bool:
        """Check if all required fields are populated."""
        return all(
            [
                self.ceo is not None,
                self.employees is not None,
                self.headquarters is not None,
                self.founded is not None,
                self.industry is not None,
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame storage."""
        return {
            "ceo": self.ceo or "",
            "employees": self.employees or "",
            "headquarters": self.headquarters or "",
            "founded": self.founded or "",
            "industry": self.industry or "",
            "sources": ",".join(self.sources) if self.sources else "",
            "urls": ",".join(self.urls) if self.urls else "",
        }


class HTTPClient:
    """Handles HTTP requests with proper error handling and retry logic."""

    def __init__(self):
        self.fake = Faker()
        self.session = requests.Session()
        self.last_request_time = 0
        self._update_headers()

    def _update_headers(self):
        """Update request headers with random user agent and more realistic headers."""
        self.fake.seed_instance(random.randint(0, 1000))
        ip = self.fake.ipv4()

        # More comprehensive and realistic headers
        self.headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "X-Forwarded-For": ip,
            "X-Real-Ip": ip,
            "X-Requested-With": "XMLHttpRequest",
        }

    def _rate_limit_delay(self):
        """Implement rate limiting to avoid 429 errors."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP GET request with improved retry logic and rate limiting."""
        self._rate_limit_delay()
        
        for attempt in range(MAX_RETRIES):
            try:
                self._update_headers()

                # Handle special cases for different domains
                if "google.com" in url:
                    kwargs["cookies"] = {"CONSENT": "YES+", "NID": "511=abc123"}
                elif "yahoo.com" in url:
                    kwargs["cookies"] = {
                        "A1": "d=AQABBJ...; Expires=Tue, 19 Jan 2038 03:14:07 GMT; Path=/; Domain=.yahoo.com; Secure; HttpOnly",
                        "A3": "d=AQABBJ...; Expires=Tue, 19 Jan 2038 03:14:07 GMT; Path=/; Domain=.yahoo.com; Secure; HttpOnly"
                    }
                elif "marketwatch.com" in url:
                    kwargs["cookies"] = {"wsod_region": "us", "wsod_language": "en"}

                response = self.session.get(
                    url, headers=self.headers, timeout=REQUEST_TIMEOUT, **kwargs
                )

                status = response.status_code
                
                # Success case
                if status < 300:
                    return response

                # Handle specific error codes
                if status == 429:  # Rate limited
                    logger.warning(f"Rate limited (429) for {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES - 1:
                        # Exponential backoff for rate limits
                        backoff = (2 ** attempt) * RATE_LIMIT_DELAY * 2
                        logger.info(f"Waiting {backoff} seconds before retry...")
                        time.sleep(backoff)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded for {url} after {MAX_RETRIES} attempts")
                        return None
                
                elif status == 403:  # Forbidden
                    logger.warning(f"Forbidden (403) for {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES - 1:
                        # Try with different headers for 403
                        self._update_headers()
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        logger.error(f"Access forbidden for {url} after {MAX_RETRIES} attempts")
                        return None
                
                elif status in (400, 401, 404, 405, 410):  # Client errors - don't retry
                    logger.info(f"HTTP {status} for {url}; skipping retries")
                    return None
                
                elif status >= 500:  # Server errors - retry with backoff
                    logger.warning(f"Server error {status} for {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES - 1:
                        backoff = (2 ** attempt) * RETRY_DELAY
                        time.sleep(backoff)
                        continue
                    else:
                        logger.error(f"Server error for {url} after {MAX_RETRIES} attempts")
                        return None

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
            ) as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                
                if attempt < MAX_RETRIES - 1:
                    backoff = (2 ** attempt) * RETRY_DELAY
                    time.sleep(backoff)
                else:
                    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
                    return None

        return None


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    @abstractmethod
    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from the source."""
        pass

    def _add_source(self, company_details: CompanyDetails, url: str):
        """Add source information to company details."""
        company_details.sources.add(self.__class__.__name__)
        company_details.urls.add(url)


class GoogleFinanceScraper(BaseScraper):
    """Scraper for Google Finance."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from Google Finance."""
        exchanges = ["NASDAQ", "NYSE"]

        for exchange in exchanges:
            url = f"https://www.google.com/finance/quote/{ticker}:{exchange}?hl=en"
            response = self.http_client.get(url)

            if response:
                soup = BeautifulSoup(response.content, "html.parser")
                if self._parse_google_finance(soup, company_details):
                    self._add_source(company_details, url)
                    break

        return company_details

    def _parse_google_finance(
        self, soup: BeautifulSoup, company_details: CompanyDetails
    ) -> bool:
        """Parse Google Finance page content."""
        found_data = False
        divs = soup.body.find_all("div", attrs={"class": "gyFHrc"})

        for div in divs:
            single_div = div.find("div", attrs={"class": "mfs7Fc"})
            if not single_div:
                continue

            value_div = div.find("div", attrs={"class": "P6K39c"})
            if not value_div:
                continue

            field_name = single_div.text.lower()
            value = value_div.text.strip()

            if field_name == "ceo" and not company_details.ceo:
                company_details.ceo = value
                found_data = True
            elif field_name == "employees" and not company_details.employees:
                company_details.employees = value
                found_data = True
            elif field_name == "headquarters" and not company_details.headquarters:
                company_details.headquarters = value
                found_data = True
            elif field_name == "founded" and not company_details.founded:
                company_details.founded = value
                found_data = True

        return found_data


def set_ip():
    Faker.seed(random.randint(0, 7))
    ip = fake.ipv4()
    headers["X-Forwarded-For"] = ip
    headers["X-Real-Ip"] = ip


def send_request(url):
    try:
        if "google.com" in url:
            res = requests.get(url, cookies={"CONSENT": "YES+"}, headers=headers)
        elif "yahoo.com" in url:
            # Simulate accepting cookies for Yahoo Finance
            res = requests.get(
                url,
                cookies={
                    "A1": "d=AQABBJ...; Expires=Tue, 19 Jan 2038 03:14:07 GMT; Path=/; Domain=.yahoo.com; Secure; HttpOnly"
                },
                headers=headers,
            )
        else:
            res = requests.get(url, headers=headers)
        if res.status_code >= 300:
            return ""
        return res
    except requests.exceptions.ConnectionError:
        return retry(url)
    except requests.exceptions.Timeout:
        return retry(url)
    except requests.exceptions.RequestException:
        return retry(url)


def retry(url, max_attempts=2):
    attempt = 0
    while attempt < max_attempts:
        try:
            set_ip()
            print("Retry Attempt {} to {}".format(attempt + 1, url))
            res = requests.get(url, headers=headers)
            return res
        except requests.exceptions.RequestException:
            time.sleep(1)
            attempt += 1
    return ""


# Fetch from Google Finance
def get_from_gfinance(url, company_details):
    set_source_url = False
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, "html.parser")

        divs = soup.body.find_all("div", attrs={"class": "gyFHrc"})
        for div in divs:
            single_div = div.find("div", attrs={"class": "mfs7Fc"})
            if single_div.text == "CEO":
                company_details["ceo"] = div.find("div", attrs={"class": "P6K39c"}).text
                set_source_url = True
            if single_div.text == "Employees":
                company_details["employees"] = div.find(
                    "div", attrs={"class": "P6K39c"}
                ).text
                set_source_url = True
            if single_div.text == "Headquarters":
                company_details["headquarters"] = div.find(
                    "div", attrs={"class": "P6K39c"}
                ).text
                set_source_url = True
            if single_div.text == "Founded":
                company_details["founded"] = div.find(
                    "div", attrs={"class": "P6K39c"}
                ).text
                set_source_url = True

    if set_source_url:
        company_details["source"].add("Google Finance")
        company_details["url"].add(url)
    return company_details


class CNBCScraper(BaseScraper):
    """Scraper for CNBC."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from CNBC."""
        url = f"https://www.cnbc.com/quotes/{ticker}?tab=profile"
        response = self.http_client.get(url)

        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            found_data = self._parse_cnbc(soup, company_details)

            if found_data:
                self._add_source(company_details, url)

        return company_details

    def _parse_cnbc(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        """Parse CNBC page content."""
        found_data = False

        # Parse CEO information
        company_officer_divs = soup.find_all("div", {"class": "CompanyProfile-officer"})
        if company_officer_divs and not company_details.ceo:
            for div in company_officer_divs:
                officer_title_div = div.find(
                    "div", {"class": "CompanyProfile-officerTitle"}
                )
                if (
                    officer_title_div
                    and "Chief Executive Officer" in officer_title_div.text
                ):
                    ceo_div = div.find("div")
                    if ceo_div:
                        company_details.ceo = ceo_div.text.strip()
                        found_data = True
                    break

        # Parse headquarters information
        headquarters_divs = soup.find_all("div", {"class": "CompanyProfile-address"})
        if headquarters_divs and not company_details.headquarters:
            for div in headquarters_divs:
                text_divs = div.find(class_=False)
                if text_divs:
                    company_details.headquarters = " ".join(
                        item.strip() for item in text_divs.find_all(text=True)
                    )
                    found_data = True
                    break

        return found_data


class CNNScraper(BaseScraper):
    """Scraper for CNN Money."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from CNN Money."""
        url = f"https://money.cnn.com/quote/profile/profile.html?symb={ticker}"
        response = self.http_client.get(url)

        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            found_data = self._parse_cnn(soup, company_details)

            if found_data:
                self._add_source(company_details, url)

        return company_details

    def _parse_cnn(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        """Parse CNN Money page content."""
        found_data = False

        # Parse CEO information
        ceo_div = soup.find("div", {"class": "wsod_DataColumnRight"})
        if ceo_div and not company_details.ceo:
            right_column_divs = ceo_div.find_all("div")
            if right_column_divs:
                top_executive_rows = right_column_divs[-1].find_all(
                    "tr", {"class": "wsod_companyOfficer"}
                )
                if (
                    len(top_executive_rows) != 1
                    and top_executive_rows[0].text
                    != "There are no executives to display."
                ):
                    for row in top_executive_rows:
                        title_td = row.find("td", {"class": "wsod_officerTitle"})
                        if title_td and "Chief Executive Officer" in title_td.text:
                            ceo_td = row.find("td")
                            if ceo_td:
                                company_details.ceo = ceo_td.text.strip()
                                found_data = True
                            break

        # Parse headquarters information
        headquarters_div = soup.find("div", {"class": "wsod_DataColumnLeft"})
        if headquarters_div and not company_details.headquarters:
            left_column_divs = headquarters_div.find_all("div")
            if left_column_divs:
                headquarters_row = left_column_divs[0].find_all(
                    "td", {"class": "wsod_companyAddress"}
                )
                for row in headquarters_row:
                    divs = row.find(
                        "div",
                        {"class": "wsod_companyContactInfo wsod_companyNameStreet"},
                    )
                    if divs:
                        company_details.headquarters = " ".join(
                            item.strip() for item in divs.find_all(text=True)
                        )
                        found_data = True
                        break

        # Parse industry information
        industry_div = soup.find("table", id="wsod_sectorIndustry")
        if industry_div and not company_details.industry:
            td_col = industry_div.find("td", class_=False)
            if td_col and "INDUSTRY" in td_col.text:
                industry_div_inner = td_col.find("div", class_=False)
                if industry_div_inner:
                    company_details.industry = industry_div_inner.text.strip()
                    found_data = True

        return found_data


class MarketWatchScraper(BaseScraper):
    """Scraper for MarketWatch."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from MarketWatch."""
        url = f"https://www.marketwatch.com/investing/stock/{ticker}/company-profile?mod=mw_quote_tab"
        response = self.http_client.get(url)

        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            found_data = self._parse_marketwatch(soup, company_details)

            if found_data:
                self._add_source(company_details, url)

        return company_details

    def _parse_marketwatch(
        self, soup: BeautifulSoup, company_details: CompanyDetails
    ) -> bool:
        """Parse MarketWatch page content."""
        found_data = False

        # Parse CEO information
        ceo_divs = soup.find_all("div", {"class": "element element--list"})
        if ceo_divs and not company_details.ceo:
            list_items = ceo_divs[0].find_all("li", {"class": "kv__item"})
            for item in list_items:
                small_tag = item.find("small")
                if small_tag and "Chief Executive Officer" in small_tag.text:
                    a_tag = item.find("a")
                    if a_tag:
                        company_details.ceo = a_tag.text.strip()
                        found_data = True
                    break

        # Parse headquarters information
        headquarters_divs = soup.find_all("div", {"class": "information"})
        if headquarters_divs and not company_details.headquarters:
            address_div = headquarters_divs[0].find("div", {"class": "address"})
            if address_div:
                company_details.headquarters = " ".join(
                    item.strip() for item in address_div.find_all(text=True)
                )
                found_data = True

        # Parse industry information
        industry_lis = soup.find_all("li", {"class": "kv__item w100"})
        if industry_lis and not company_details.industry:
            for li in industry_lis:
                small_tag = li.find("small")
                if small_tag and "Industry" in small_tag.text:
                    span_tag = li.find("span")
                    if span_tag:
                        company_details.industry = span_tag.text.strip()
                        found_data = True
                    break

        # Parse employees information
        employees_ulis = soup.find_all("ul", {"class": "list list--kv list--col50"})
        if employees_ulis and not company_details.employees:
            lis = employees_ulis[0].find_all("li", "kv__item")
            for li in lis:
                small_tag = li.find("small")
                if small_tag and "Employees" in small_tag.text:
                    span_tag = li.find("span")
                    if span_tag:
                        company_details.employees = span_tag.text.strip()
                        found_data = True
                    break

        return found_data


class YahooFinanceScraper(BaseScraper):
    """Scraper for Yahoo Finance."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from Yahoo Finance."""
        # Use explicit query param pattern to avoid occasional 404s
        url = f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}"
        response = self.http_client.get(url)

        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            found_data = self._parse_yahoo_finance(soup, company_details)

            if found_data:
                self._add_source(company_details, url)

        return company_details

    def _parse_yahoo_finance(
        self, soup: BeautifulSoup, company_details: CompanyDetails
    ) -> bool:
        """Parse Yahoo Finance page content."""
        found_data = False

        # Parse CEO information
        ceo_data_table_body = soup.find_all("tbody")
        if ceo_data_table_body and not company_details.ceo:
            tr_list = ceo_data_table_body[0].find_all("tr")
            for tr in tr_list:
                td_list = tr.find_all("td")
                if len(td_list) > 1:
                    span_tag = td_list[1].find("span")
                    if span_tag:
                        text = span_tag.text
                        if text and ("Chief Exec. Officer" in text or "CEO" in text):
                            ceo_span = td_list[0].find("span")
                            if ceo_span:
                                company_details.ceo = ceo_span.text.strip()
                                found_data = True
                            break

        # Parse company details
        details_div = soup.find("div", "asset-profile-container")
        if details_div:
            p_tags = details_div.find_all("p")
            for p in p_tags:
                if p.span:
                    for span in p.find_all("span"):
                        span_text = span.text
                        if "Industry" in span_text and not company_details.industry:
                            next_span = span.find_next("span", class_=True)
                            if next_span:
                                company_details.industry = next_span.text.strip()
                                found_data = True
                        elif (
                            "Full Time Employees" in span_text
                            and not company_details.employees
                        ):
                            next_span = span.find_next("span", class_=True)
                            if next_span:
                                company_details.employees = next_span.text.strip()
                                found_data = True
                else:
                    if p.text and not company_details.headquarters:
                        company_details.headquarters = p.text.strip()
                        found_data = True

        return found_data


class CompanyDetailsFetcher:
    """Main class for fetching company details from multiple sources."""

    def __init__(self, max_workers: int = None):
        """Initialize the fetcher with HTTP client and scrapers."""
        self.http_client = HTTPClient()
        # Default scrapers (exclude CNN by default due to frequent 404/structure changes)
        self.scrapers = [
            GoogleFinanceScraper(self.http_client),
            CNBCScraper(self.http_client),
            MarketWatchScraper(self.http_client),
            YahooFinanceScraper(self.http_client),
        ]
        # Use more conservative worker count to avoid rate limiting
        self.max_workers = max_workers or min(4, (os.cpu_count() or 1))
        # Rate limiting state
        self.rate_limit_count = 0
        self.last_rate_limit_time = 0

    def fetch_company_details(self, ticker: str) -> CompanyDetails:
        """Fetch company details from all available sources."""
        company_details = CompanyDetails()
        ticker = self._clean_ticker(ticker)

        logger.info(f"Fetching details for ticker: {ticker}")

        # Check if we're in a rate limit cooldown period
        current_time = time.time()
        if self.rate_limit_count > 3 and current_time - self.last_rate_limit_time < 300:  # 5 minutes
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
            except Exception as e:
                logger.error(
                    f"Error scraping {ticker} with {scraper.__class__.__name__}: {e}"
                )
                # If we get rate limited, update our state
                if "429" in str(e) or "rate limit" in str(e).lower():
                    self.rate_limit_count += 1
                    self.last_rate_limit_time = current_time
                continue

        return company_details

    def fetch_multiple_companies(self, tickers: list) -> Dict[str, CompanyDetails]:
        """Fetch details for multiple companies using ThreadPoolExecutor."""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(self.fetch_company_details, ticker): ticker
                for ticker in tickers
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    results[ticker] = future.result()
                    # Add small delay between processing results to avoid overwhelming servers
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                    results[ticker] = CompanyDetails()

        return results

    def _clean_ticker(self, ticker: str) -> str:
        """Clean ticker symbol by removing special characters."""
        # Remove ^ and / characters
        ticker = ticker.replace("^", "").replace("/", "")
        return ticker.strip()


# Legacy function for backward compatibility
def get_from_gfinance_nasdaq(ticker, company_details):
    """Legacy function - use CompanyDetailsFetcher instead."""
    fetcher = CompanyDetailsFetcher()
    return fetcher.fetch_company_details(ticker)


def get_from_gfinance_nyse(ticker, company_details):
    """Legacy function - use CompanyDetailsFetcher instead."""
    fetcher = CompanyDetailsFetcher()
    return fetcher.fetch_company_details(ticker)


def get_from_cnbc(ticker, company_details):
    """Legacy function - use CompanyDetailsFetcher instead."""
    fetcher = CompanyDetailsFetcher()
    return fetcher.fetch_company_details(ticker)


def get_from_cnn(ticker, company_details):
    """Legacy function - use CompanyDetailsFetcher instead."""
    fetcher = CompanyDetailsFetcher()
    return fetcher.fetch_company_details(ticker)


def get_from_market_watch(ticker, company_details):
    """Legacy function - use CompanyDetailsFetcher instead."""
    fetcher = CompanyDetailsFetcher()
    return fetcher.fetch_company_details(ticker)


def get_from_yahoo_finance(ticker, company_details):
    """Legacy function - use CompanyDetailsFetcher instead."""
    fetcher = CompanyDetailsFetcher()
    return fetcher.fetch_company_details(ticker)
