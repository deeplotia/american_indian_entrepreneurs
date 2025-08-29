from bs4 import BeautifulSoup

from src.models.company_details import CompanyDetails
from src.scrapers.base import BaseScraper


class CNNScraper(BaseScraper):
    """Scraper for CNN Money."""

    def scrape(self, ticker: str, company_details: CompanyDetails) -> CompanyDetails:
        url = f"https://money.cnn.com/quote/profile/profile.html?symb={ticker}"
        response = self.http_client.get(url)
        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            if self._parse(soup, company_details):
                self._add_source(company_details, url)
        return company_details

    def _parse(self, soup: BeautifulSoup, company_details: CompanyDetails) -> bool:
        found = False

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
                                found = True
                            break

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
                        found = True
                        break

        industry_div = soup.find("table", id="wsod_sectorIndustry")
        if industry_div and not company_details.industry:
            td_col = industry_div.find("td", class_=False)
            if td_col and "INDUSTRY" in td_col.text:
                industry_div_inner = td_col.find("div", class_=False)
                if industry_div_inner:
                    company_details.industry = industry_div_inner.text.strip()
                    found = True

        return found


