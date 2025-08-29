from bs4 import BeautifulSoup

from src.models.company_details import CompanyDetails
from src.scrapers.base import BaseScraper


class MarketWatchScraper(BaseScraper):
    """Scraper for MarketWatch."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        url = (
            f"https://www.marketwatch.com/investing/stock/{ticker}/company-profile"
        )
        response = self.http_client.get(url)
        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            if self._parse(soup, company_details):
                self._add_source(company_details, url)
        return company_details

    def _parse(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        found = False

        ceo_divs = soup.find_all("div", {"class": "element element--list"})
        if ceo_divs and not company_details.ceo:
            list_items = ceo_divs[0].find_all("li", {"class": "kv__item"})
            for item in list_items:
                small_tag = item.find("small")
                if small_tag and "Chief Executive Officer" in small_tag.text:
                    a_tag = item.find("a")
                    if a_tag:
                        company_details.ceo = a_tag.text.strip()
                        found = True
                    break

        headquarters_divs = soup.find_all("div", {"class": "information"})
        if headquarters_divs and not company_details.headquarters:
            address_div = headquarters_divs[0].find("div", {"class": "address"})
            if address_div:
                company_details.headquarters = " ".join(
                    item.strip() for item in address_div.find_all(text=True)
                )
                found = True

        industry_lis = soup.find_all("li", {"class": "kv__item w100"})
        if industry_lis and not company_details.industry:
            for li in industry_lis:
                small_tag = li.find("small")
                if small_tag and "Industry" in small_tag.text:
                    span_tag = li.find("span")
                    if span_tag:
                        company_details.industry = span_tag.text.strip()
                        found = True
                    break

        employees_ulis = soup.find_all("ul", {"class": "list list--kv list--col50"})
        if employees_ulis and not company_details.employees:
            lis = employees_ulis[0].find_all("li", "kv__item")
            for li in lis:
                small_tag = li.find("small")
                if small_tag and "Employees" in small_tag.text:
                    span_tag = li.find("span")
                    if span_tag:
                        company_details.employees = span_tag.text.strip()
                        found = True
                    break

        return found


