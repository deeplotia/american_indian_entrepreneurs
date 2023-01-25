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


def set_ip():
    Faker.seed(random.randint(0, 7))
    ip = fake.ipv4()
    headers['X-Forwarded-For'] = ip
    headers['X-Real-Ip'] = ip


def send_request(url):
    try:
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
def get_from_gfinance(url):
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')
        divs = soup.body.find_all("div", attrs={"class": "gyFHrc"})
        for div in divs:
            ceo_div = div.find("div", attrs={"class": "mfs7Fc"})
            if ceo_div.text == "CEO":
                ceo_name_div = div.find("div", attrs={"class": "P6K39c"})
                return ceo_name_div.text, "Google Finance", url
    return None, None, None


# Fetch from Google Finance (listed under NASDAQ)
def get_from_gfinance_nasdaq(ticker):
    url = "https://www.google.com/finance/quote/" + str(ticker) + ":NASDAQ?hl=en"
    return get_from_gfinance(url)


# Fetch from Google Finance (listed under NYSE)
def get_from_gfinance_nyse(ticker):
    url = "https://www.google.com/finance/quote/" + str(ticker) + ":NYSE?hl=en"
    return get_from_gfinance(url)


# Get from CNBC
def get_from_cnbc(ticker: str):
    url = "https://www.cnbc.com/quotes/" + ticker
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')
        company_officer_divs = soup.find_all("div", {"class": "CompanyProfile-officer"})
        for div in company_officer_divs:
            officer_title_div = div.find("div", {"class": "CompanyProfile-officerTitle"})
            if "Chief Executive Officer" in officer_title_div.text:
                return div.find("div").text, "CNBC", url
    return None, None, None


# Get from CNN
def get_from_cnn(ticker: str):
    url = "https://money.cnn.com/quote/profile/profile.html?symb=" + ticker
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')
        data_div = soup.find("div", {"class": "wsod_DataColumnRight"})
        if data_div:
            right_column_divs = data_div.find_all("div")
            top_executive_rows = right_column_divs[-1].find_all("tr", {"class": "wsod_companyOfficer"})
            if len(top_executive_rows) == 1 and top_executive_rows[0].text == "There are no executives to display.":
                return None, None, None
            for row in top_executive_rows:
                if "Chief Executive Officer" in row.find("td", {"class": "wsod_officerTitle"}).text:
                    return row.td.text, "CNN", url

    return None, None, None


# Fetch from marketwatch
def get_from_market_watch(ticker: str):
    url = "https://www.marketwatch.com/investing/stock/{ticker}/company-profile?mod=mw_quote_tab".format(ticker=ticker)
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')
        element_div = soup.find_all("div", {"class": "element element--list"})
        if len(element_div) == 0:
            return None, None, None
        list_items = element_div[0].find_all("li", {"class": "kv__item"})
        for item in list_items:
            if "Chief Executive Officer" in item.small.text:
                return item.a.text, "Market Watch", url
    return None, None, None


# Fetch from yahoo finance
def get_from_yahoo_finance(ticker: str):
    url = "https://finance.yahoo.com/quote/{ticker}/profile".format(ticker=ticker)
    set_ip()
    res = send_request(url)
    if res:
        soup = BeautifulSoup(res.content, 'html.parser')
        data_table_body = soup.find_all("tbody")
        if len(data_table_body) == 0:
            return None, None, None
        tr_list = data_table_body[0].find_all("tr")
        for tr in tr_list:
            td_list = tr.find_all("td")
            if len(td_list) > 1:
                if td_list[1].span is not None:
                    text = td_list[1].span.text
                    if text is not None and ("Chief Exec. Officer" in text or "CEO" in text):
                        return td_list[0].span.text, "Yahoo Finance", url

    return None, None, None
