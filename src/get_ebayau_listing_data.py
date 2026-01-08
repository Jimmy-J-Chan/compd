import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import streamlit as st

def get_chrome_driver(headless=True):
    # Set up Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Uncomment to run without a visible window
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("window-size=1280,800")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def close_chrome_driver(driver):
    driver.quit()
    pass

def parse_lsts(lsts):
    cols = ['sol']
    dfls = pd.DataFrame()
    for ix, lst in enumerate(lsts):
        # contents
        cts = lst.find(class_="su-card-container__content")

        # header
        hdr = cts.find(class_="su-card-container__header")
        dfls.loc[ix, 'sold_date'] = hdr.find(class_="s-card__caption").text
        title_contents = hdr.find(class_="s-card__link").find(class_="s-card__title").contents
        dfls.loc[ix, 'title'] = title_contents[1].text if len(title_contents)>2 else title_contents[0].text
        dfls.loc[ix,'sold_url'] = hdr.find(class_="s-card__link").attrs['href']

        # attributes
        attr_p = cts.find(class_="su-card-container__attributes__primary")
        attrs_p = [t.text for t in attr_p.find_all('div')]
        dfls.loc[ix, 'price_str'] = attrs_p[0]
        dfls.loc[ix, 'auction_type_str'] = attrs_p[1]
        from_ctry_strs = [c for c in attrs_p if c.startswith('from ')]
        dfls.loc[ix, 'from_ctry_str'] = from_ctry_strs[0] if len(from_ctry_strs)>0 else ''

        attr_s = cts.find(class_="su-card-container__attributes__secondary")
        attrs_s = [t.text for t in attr_s.find_all('span')]
        dfls.loc[ix, 'seller_name'] = attrs_s[0]
        dfls.loc[ix, 'seller_rating'] = attrs_s[1]

        # images
        media = lst.find(class_="su-card-container__media")
        img_url_base = media.find(class_='s-card__link image-treatment').find('img').attrs['src']
        dfls.loc[ix, 'img_url0'] = img_url_base.rsplit('/', 1)[0]

        # img sizes
        # 140w  - /s-l140.webp
        # 500w  - /s-l500.webp
        # 960w  - /s-l960.webp
        # 1600w - /s-l1600.webp

    # parse cols
    dfls['auction_type'] = None
    mask = dfls['auction_type_str'].isin(["or Best Offer","Buy It Now"])
    dfls.loc[mask,'auction_type'] = 'Buy It Now'
    mask = dfls['auction_type_str'].str.contains('bid|bids')
    dfls.loc[mask,'auction_type'] = 'Auction'
    mask = dfls['auction_type_str']=='Best Offer accepted'
    dfls.loc[mask,'auction_type'] = 'Best Offer'

    dfls['sold_date'] = pd.to_datetime(dfls['sold_date'].str.strip('Sold '))
    dfls['price'] = None
    dfls['num_p'] = dfls['price_str'].str.split('AU').str.len()-1

    mask = dfls['auction_type_str'].isin(['or Best Offer','Buy It Now','Best Offer accepted'])
    mask = mask | (dfls['auction_type_str'].str.contains('bid|bids'))
    mask = mask != (dfls['price_str'].str.contains('to'))
    mask = mask & (dfls['num_p']==1)
    dfls.loc[mask, 'price'] = dfls.loc[mask, 'price_str'].str.replace('AU $','').str.replace(',','').astype(float)
    # if price drops
    mask = (dfls['num_p']>1) & (dfls['auction_type_str']=='Best Offer accepted')
    dfls.loc[mask,'price'] = dfls.loc[mask]['price_str'].str.split('AU', expand=True)[1]
    dfls.loc[mask, 'price'] = dfls.loc[mask,'price'].str.replace(r'[$, ]', '', regex=True).astype(float)
    dfls['price'] = dfls['price'].astype(float)

    # sort by sold date desc
    dfls = dfls.sort_values(by='sold_date', ascending=False)
    return dfls

@st.cache_data
def get_lst_imgs(url, _driver):
    # go to sold listing url
    driver = _driver
    driver.get(url)

    try:
        # wait until links loaded
        element = WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CLASS_NAME, "x-item-condensed-card__message")))

        # get urls
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        mstr_container = soup.find(class_="center-panel-container vi-mast")
        img_container = mstr_container.find(class_="ux-image-grid no-scrollbar")
        img_urls = [t.attrs['src'].rsplit('/', 1)[0] for t in img_container.find_all('img')]
    except:
        img_urls = []
    return img_urls

@st.cache_data
def get_ebayau_listing_data(sch_phrase, item_loc, _driver):
    if len(sch_phrase)==0:
        return pd.DataFrame()
    driver = _driver

    # prep url - using selected params #TODO
    url = 'https://www.ebay.com.au/sch/i.html?_nkw=giratina+v+186%2F196&LH_Sold=1&LH_Complete=1&LH_PrefLoc=1&_sop=13&_ipg=60'

    #driver = get_chrome_driver()
    driver.get(url)

    # Wait a few seconds for JavaScript to load the price data
    time.sleep(3)

    # Get the page source and hand it over to BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    all_lsts = soup.find_all('ul', class_='srp-results srp-list clearfix')[0].find_all('li')
    lsts = [l for l in all_lsts if 'id' in l.attrs.keys()]

    # parse all listings into a df - include links to images
    dfls = parse_lsts(lsts)

    # remove int sales listings if au only
    if item_loc in ['Australia only']:
        mask = dfls['from_ctry_str'].str.len()==0
        dfls = dfls.loc[mask]
    return dfls


if __name__ == '__main__':
    driver = get_chrome_driver(headless=False)
    sch_phrase = 'giratina v 186/196'
    item_loc = 'Australia only'
    get_ebayau_listing_data(sch_phrase, item_loc, driver)

    # driver = get_chrome_driver()
    # url = 'https://www.ebay.com.au/itm/317727178443?_skw=giratina+v+186%2F196&itmmeta=01KE8KFSS30HS8C6CRQE62W06X&hash=item49fa03fecb:g:--YAAeSwodFpWOh7&itmprp=enc%3AAQAKAAAA0FkggFvd1GGDu0w3yXCmi1fgrAIPHOk9DlHlaOkucmPMcTYVGz%2FKDGLukugIltBoiMCVThjlRV2c6lv52hAxYWJm60JK4Lsa2gOZ3FIo9Bh06xkGKUmfTtrjOF6f7xP9VgPNsMh62mgSebSoiRTfXqBr%2BQbIxqoCB1NKb9WBBZhDpElzgKrG9ZJpy29AZN7OxX7aiP4DdDzSx7aHjcvWtxkrL9%2B2jJyFsqeu1g9Xsdj8LVkWQIQl7PpZT%2B%2BL0ioUGXt6NWZTUsPy9Sc6OpnOjwU%3D%7Ctkp%3ABk9SR9ycv5PyZg'
    # img_urls = get_lst_imgs(url, driver)
    pass


