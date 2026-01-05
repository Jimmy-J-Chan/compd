import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def get_ebayau_listing_data(sch_phrase):
    url = 'https://www.ebay.com.au/sch/i.html?_nkw=giratina+v+186%2F196&LH_Sold=1&LH_Complete=1&LH_PrefLoc=1&_sop=13&_ipg=60'

    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run without a visible window
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("window-size=1280,800")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(url)

    # Wait a few seconds for JavaScript to load the price data
    time.sleep(3)

    # Get the page source and hand it over to BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    all_lsts = soup.find_all('ul', class_='srp-results srp-list clearfix')[0].find_all('li')
    lsts = [l for l in all_lsts if 'id' in l.attrs.keys()]

    return dfls


if __name__ == '__main__':
    sch_phrase = 'giratina v 186/196'
    get_ebayau_listing_data(sch_phrase)
    pass


