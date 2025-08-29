from bs4 import BeautifulSoup

from src.models.company_details import CompanyDetails
from src.scrapers.base import BaseScraper


class GoogleFinanceScraper(BaseScraper):
    """Scraper for Google Finance."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        exchanges = ["NASDAQ", "NYSE"]
        for exchange in exchanges:
            url = f"https://www.google.com/finance/quote/{ticker}:{exchange}?hl=en"
            response = self.http_client.get(url)
            if response:
                soup = BeautifulSoup(response.content, "html.parser")
                if self._parse(soup, company_details):
                    self._add_source(company_details, url)
                    break
        return company_details

    def _parse(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        found = False
        divs = soup.body.find_all("div", attrs={"class": "gyFHrc"})
        for div in divs:
            label_div = div.find("div", attrs={"class": "mfs7Fc"})
            if not label_div:
                continue
            value_div = div.find("div", attrs={"class": "P6K39c"})
            if not value_div:
                continue
            field_name = label_div.text.lower()
            value = value_div.text.strip()
            if field_name == "ceo" and not company_details.ceo:
                company_details.ceo = value
                found = True
            elif field_name == "employees" and not company_details.employees:
                company_details.employees = value
                found = True
            elif field_name == "headquarters" and not company_details.headquarters:
                company_details.headquarters = value
                found = True
            elif field_name == "founded" and not company_details.founded:
                company_details.founded = value
                found = True
        return found


