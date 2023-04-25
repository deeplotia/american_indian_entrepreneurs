import random
import time

import requests
from bs4 import BeautifulSoup
from faker import Faker

fake = Faker()
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36'
]

headers = {
    'accept': '*/*',
    'User-Agent': random.choice(user_agents),
    'Accept-Language': 'en-US,en;',
    'referer': 'https://www.google.com/',
    'X-Forwarded-For': "",
    'X-Real-Ip': ""
}
find_year_patter = "founded in"


def set_ip():
    Faker.seed(random.randint(0, 7))
    ip = fake.ipv4()
    headers['X-Forwarded-For'] = ip
    headers['X-Real-Ip'] = ip


def send_request(url):
    try:
        if 'google.com' in url:
            res = requests.get(url, cookies={'CONSENT': 'YES+'}, headers=headers)
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
        soup = BeautifulSoup(res.content, 'html.parser')

        divs = soup.body.find_all("div", attrs={"class": "gyFHrc"})
        for div in divs:
            single_div = div.find("div", attrs={"class": "mfs7Fc"})
            if single_div.text == "CEO":
                company_details["ceo"] = div.find("div", attrs={"class": "P6K39c"}).text
                set_source_url = True
            if single_div.text == "Employees":
                company_details["employees"] = div.find("div", attrs={"class": "P6K39c"}).text
                set_source_url = True
            if single_div.text == "Headquarters":
                company_details["headquarters"] = div.find("div", attrs={"class": "P6K39c"}).text
                set_source_url = True
            if single_div.text == "Founded":
                company_details["founded"] = div.find("div", attrs={"class": "P6K39c"}).text
                set_source_url = True

    if set_source_url:
        company_details["source"].add("Google Finance")
        company_details["url"].add(url)
    return company_details


# Fetch from Google Finance (listed under NASDAQ)
def get_from_gfinance_nasdaq(ticker, company_details):
    url = "https://www.google.com/finance/quote/" + str(ticker) + ":NASDAQ?hl=en"
    return get_from_gfinance(url, company_details)


# Fetch from Google Finance (listed under NYSE)
def get_from_gfinance_nyse(ticker, company_details):
    url = "https://www.google.com/finance/quote/" + str(ticker) + ":NYSE?hl=en"
    return get_from_gfinance(url, company_details)


# Get from CNBC
def get_from_cnbc(ticker: str, company_details):
    set_source_url = False
    url = "https://www.cnbc.com/quotes/" + ticker
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')

        company_officer_divs = soup.find_all("div", {"class": "CompanyProfile-officer"})
        if company_officer_divs and company_details["ceo"] is None:
            for div in company_officer_divs:
                officer_title_div = div.find("div", {"class": "CompanyProfile-officerTitle"})
                if "Chief Executive Officer" in officer_title_div.text:
                    company_details["ceo"] = div.find("div").text
                    set_source_url = True
                break

        headquarters_divs = soup.find_all("div", {"class": "CompanyProfile-address"})
        if headquarters_divs and company_details["headquarters"] is None:
            for div in headquarters_divs:
                text_divs = div.find(class_=False)
                company_details["headquarters"] = " ".join(item.strip() for item in text_divs.find_all(text=True))
                set_source_url = True
                break

    if set_source_url:
        company_details["source"].add("CNBC")
        company_details["url"].add(url)
    return company_details


# Get from CNN
def get_from_cnn(ticker: str, company_details):
    set_source_url = False
    url = "https://money.cnn.com/quote/profile/profile.html?symb=" + ticker
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')

        ceo_div = soup.find("div", {"class": "wsod_DataColumnRight"})
        if ceo_div and company_details["ceo"] is None:
            right_column_divs = ceo_div.find_all("div")
            top_executive_rows = right_column_divs[-1].find_all("tr", {"class": "wsod_companyOfficer"})
            if len(top_executive_rows) != 1 and top_executive_rows[0].text != "There are no executives to display.":
                for row in top_executive_rows:
                    if "Chief Executive Officer" in row.find("td", {"class": "wsod_officerTitle"}).text:
                        company_details["ceo"] = row.td.text
                        set_source_url = True
                    break

        headquarters_div = soup.find("div", {"class": "wsod_DataColumnLeft"})
        if headquarters_div and company_details["headquarters"] is None:
            left_column_divs = headquarters_div.find_all("div")
            headquarters_row = left_column_divs[0].find_all("td", {"class": "wsod_companyAddress"})
            for row in headquarters_row:
                divs = row.find("div", {"class": "wsod_companyContactInfo wsod_companyNameStreet"})
                company_details["headquarters"] = " ".join(item.strip() for item in divs.find_all(text=True))
                set_source_url = True
                break

        industry_div = soup.find("table", id="wsod_sectorIndustry")
        if industry_div and company_details["industry"] is None:
            td_col = industry_div.find("td", class_=False)
            if td_col and 'INDUSTRY' in td_col:
                company_details["industry"] = td_col.find("div", class_=False).text
                set_source_url = True

    if set_source_url:
        company_details["source"].add("CNN")
        company_details["url"].add(url)
    return company_details


# Fetch from marketwatch
def get_from_market_watch(ticker: str, company_details):
    set_source_url = False
    url = "https://www.marketwatch.com/investing/stock/{ticker}/company-profile?mod=mw_quote_tab".format(ticker=ticker)
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')

        ceo_div = soup.find_all("div", {"class": "element element--list"})
        if len(ceo_div) != 0 and company_details["ceo"] is None:
            list_items = ceo_div[0].find_all("li", {"class": "kv__item"})
            for item in list_items:
                if "Chief Executive Officer" in item.small.text:
                    company_details["ceo"] = item.a.text
                    set_source_url = True
                break

        headquarters_div = soup.find_all("div", {"class": "information"})
        if headquarters_div and company_details["headquarters"] is None:
            address_div = headquarters_div[0].find("div", {"class": "address"})
            if address_div:
                company_details["headquarters"] = " ".join(item.strip() for item in address_div.find_all(text=True))
                set_source_url = True

        industry_lis = soup.find_all("li", {"class": "kv__item w100"})
        if industry_lis and company_details["industry"] is None:
            for li in industry_lis:
                if 'Industry' in li.small.text:
                    company_details["industry"] = li.span.text
                    set_source_url = True
                break

        employees_ulis = soup.find_all("ul", {"class": "list list--kv list--col50"})
        if employees_ulis and company_details["employees"] is None:
            lis = employees_ulis[0].find_all("li", "kv__item")
            for li in lis:
                if 'Employees' in li.small.text:
                    company_details["employees"] = li.span.text
                    set_source_url = True

    if set_source_url:
        company_details["source"].add("Market Watch")
        company_details["url"].add(url)
    return company_details


# Fetch from yahoo finance
def get_from_yahoo_finance(ticker: str, company_details):
    set_source_url = False
    url = "https://finance.yahoo.com/quote/{ticker}/profile".format(ticker=ticker)
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')

        ceo_data_table_body = soup.find_all("tbody")
        if len(ceo_data_table_body) != 0 and company_details["ceo"] is None:
            tr_list = ceo_data_table_body[0].find_all("tr")
            for tr in tr_list:
                td_list = tr.find_all("td")
                if len(td_list) > 1:
                    if td_list[1].span is not None:
                        text = td_list[1].span.text
                        if text is not None and ("Chief Exec. Officer" in text or "CEO" in text):
                            company_details["ceo"] = td_list[0].span.text
                            set_source_url = False
                break

        details_div = soup.find("div", "asset-profile-container")
        if details_div:
            p_tags = details_div.find_all("p")
            for p in p_tags:
                if p.span:
                    for span in p.find_all("span"):
                        if 'Industry' in span.text and company_details["industry"] is None:
                            company_details["industry"] = span.find_next("span", class_=True).text
                            set_source_url = False
                        if 'Full Time Employees' in span.text and company_details["employees"] is None:
                            company_details["employees"] = span.find_next("span", class_=True).text
                            set_source_url = False
                else:
                    if p.text:
                        company_details["headquarters"] = p.text

    if set_source_url:
        company_details["source"].add("Yahoo Finance")
        company_details["url"].add(url)
    return company_details
