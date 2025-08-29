from bs4 import BeautifulSoup

from src.models.company_details import CompanyDetails
from src.scrapers.base import BaseScraper


class YahooFinanceScraper(BaseScraper):
    """Scraper for Yahoo Finance."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        url = f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}"
        response = self.http_client.get(url)
        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            if self._parse(soup, company_details):
                self._add_source(company_details, url)
        return company_details

    def _parse(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        found = False

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
                                found = True
                            break

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
                                found = True
                        elif (
                            "Full Time Employees" in span_text
                            and not company_details.employees
                        ):
                            next_span = span.find_next("span", class_=True)
                            if next_span:
                                company_details.employees = next_span.text.strip()
                                found = True
                else:
                    if p.text and not company_details.headquarters:
                        company_details.headquarters = p.text.strip()
                        found = True

        return found


