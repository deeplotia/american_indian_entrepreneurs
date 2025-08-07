from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Initialize Selenium WebDriver
def init_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no browser UI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service("/path/to/chromedriver")  # Replace with the path to your ChromeDriver
    return webdriver.Chrome(service=service, options=options)

# Fetch data from Google Finance using Selenium
def get_from_gfinance_selenium(url, company_details):
    driver = init_driver()
    try:
        driver.get(url)
        time.sleep(3)  # Wait for the page to load

        # Accept cookies if the consent popup appears
        try:
            accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'I agree')]")
            accept_button.click()
            time.sleep(2)  # Wait for the page to reload after accepting cookies
        except Exception:
            pass  # No cookie popup found

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract company details
        divs = soup.body.find_all("div", attrs={"class": "gyFHrc"})
        for div in divs:
            single_div = div.find("div", attrs={"class": "mfs7Fc"})
            if single_div and single_div.text == "CEO":
                company_details["ceo"] = div.find("div", attrs={"class": "P6K39c"}).text
            if single_div and single_div.text == "Employees":
                company_details["employees"] = div.find("div", attrs={"class": "P6K39c"}).text
            if single_div and single_div.text == "Headquarters":
                company_details["headquarters"] = div.find("div", attrs={"class": "P6K39c"}).text
            if single_div and single_div.text == "Founded":
                company_details["founded"] = div.find("div", attrs={"class": "P6K39c"}).text

        # Add source and URL
        company_details["source"].add("Google Finance")
        company_details["url"].add(url)

    except Exception as e:
        print(f"[Error] Failed to fetch data from Google Finance: {e}")
    finally:
        driver.quit()  # Ensure the browser is closed
    return company_details