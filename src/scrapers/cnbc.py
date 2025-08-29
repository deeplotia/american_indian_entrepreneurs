from bs4 import BeautifulSoup

from src.models.company_details import CompanyDetails
from src.scrapers.base import BaseScraper


class CNBCScraper(BaseScraper):
    """Scraper for CNBC."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        url = f"https://www.cnbc.com/quotes/{ticker}"
        response = self.http_client.get(url)
        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            if self._parse(soup, company_details):
                self._add_source(company_details, url)
        return company_details

    def _parse(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        found = False
        officer_divs = soup.find_all("div", {"class": "CompanyProfile-officer"})
        if officer_divs and not company_details.ceo:
            for div in officer_divs:
                title_div = div.find("div", {"class": "CompanyProfile-officerTitle"})
                if title_div and "Chief Executive Officer" in title_div.text:
                    ceo_div = div.find("div")
                    if ceo_div:
                        company_details.ceo = ceo_div.text.strip()
                        found = True
                    break

        headquarters_divs = soup.find_all("div", {"class": "CompanyProfile-address"})
        if headquarters_divs and not company_details.headquarters:
            for div in headquarters_divs:
                text_divs = div.find(class_=False)
                if text_divs:
                    company_details.headquarters = " ".join(
                        item.strip() for item in text_divs.find_all(text=True)
                    )
                    found = True
                    break

        return found


