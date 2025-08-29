from abc import ABC, abstractmethod

from src.http.http_client import HTTPClient
from src.models.company_details import CompanyDetails


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    @abstractmethod
    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        """Scrape company details from the source."""
        raise NotImplementedError

    def _add_source(self, company_details: CompanyDetails, url: str):
        company_details.sources.add(self.__class__.__name__)
        company_details.urls.add(url)


