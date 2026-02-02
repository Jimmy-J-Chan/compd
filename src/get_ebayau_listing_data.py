import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import streamlit as st
from src.common import get_chrome_driver, encode_str
#import urllib.parse

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
        dfls.loc[ix, 'sold_date_str'] = hdr.find(class_="s-card__caption").text
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

    dfls['sold_date'] = pd.to_datetime(dfls['sold_date_str'].str.strip('Sold '), format='mixed')
    dfls['price'] = None
    dfls['num_p'] = dfls['price_str'].str.split('AU').str.len()-1

    mask = dfls['auction_type_str'].isin(['or Best Offer','Buy It Now','Best Offer accepted'])
    mask = mask | (dfls['auction_type_str'].str.contains('bid|bids'))
    mask = mask != (dfls['price_str'].str.contains('to'))
    mask = mask & (dfls['num_p']==1)
    dfls.loc[mask, 'price'] = dfls.loc[mask, 'price_str'].str.replace('AU $','').str.replace(',','').astype(float)
    # if price drops
    mask = (dfls['num_p']>1) & (dfls['auction_type_str']=='Best Offer accepted')
    if mask.sum()>0:
        dfls.loc[mask,'price'] = dfls.loc[mask]['price_str'].str.split('AU', expand=True)[1]
        dfls.loc[mask, 'price'] = dfls.loc[mask,'price'].str.replace(r'[$, ]', '', regex=True).astype(float)
    dfls['price'] = dfls['price'].astype(float)

    # sort by sold date desc
    dfls = dfls.sort_values(by='sold_date', ascending=False)

    # keep best matches at top?
    return dfls

@st.cache_data(ttl='1hr',max_entries=15,show_spinner=False)
def get_lst_imgs(url, _driver):
    # go to sold listing url
    driver = _driver
    driver.get(url)

    try:
        # wait until - gh-search-button__label
        #element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "x-item-condensed-card__message")))
        element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "gh-search-button__label")))

        # get urls
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        mstr_container = soup.find(class_="center-panel-container vi-mast")
        img_container = mstr_container.find(class_="ux-image-grid no-scrollbar").find_all('img')

        # src or data-src
        img_urls = [t.attrs['src'] if 'src' in t.attrs.keys() else t.attrs['data-src'] for t in img_container]
        img_urls = [t.rsplit('/', 1)[0] for t in img_urls]
    except:
        img_urls = []
    return img_urls

@st.cache_data(ttl='1hr',max_entries=15,show_spinner=True)
def get_ebayau_listing_data(sch_phrase, item_loc, ipg, _driver):
    if len(sch_phrase)==0:
        return pd.DataFrame()
    if ipg not in [60,120,180]:
        return pd.DataFrame()
    driver = _driver

    # encode url
    base_url = r'https://www.ebay.com.au/sch/i.html?'
    enc_sch_phrase = encode_str(sch_phrase, r"_nkw")
    param_sold = '&LH_Sold=1&LH_Complete=1'
    param_item_loc = '&LH_PrefLoc=1' if item_loc=='Australia only' else '&LH_PrefLoc=2' #worldwide
    param_sort = '&_sop=13' # sort: ended recently
    param_ipp = f'&_ipg={int(ipg)}' # items per page
    url = f"{base_url}{enc_sch_phrase}{param_sold}{param_item_loc}{param_sort}{param_ipp}"
    #url = 'https://www.ebay.com.au/sch/i.html?_nkw=giratina+v+186%2F196&LH_Sold=1&LH_Complete=1&LH_PrefLoc=1&_sop=13&_ipg=60'

    #driver = get_chrome_driver()
    driver.get(url)

    # Wait a few seconds for JavaScript to load the price data
    time.sleep(3)

    # Get the page source and hand it over to BeautifulSoup
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_lsts = soup.find_all('ul', class_='srp-results srp-list clearfix')[0].find_all('li')
        lsts = [l for l in all_lsts if 'id' in l.attrs.keys()]
        if len(lsts)==0:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

    # parse all listings into a df - include links to images
    dfls = parse_lsts(lsts)

    # remove int sales listings if au only
    if item_loc in ['Australia only']:
        mask = dfls['from_ctry_str'].str.len()==0
        dfls = dfls.loc[mask]
    return dfls


if __name__ == '__main__':
    driver = get_chrome_driver(headless=False, use_local=True)
    # sch_phrase = 'giratina v 186/196'
    sch_phrase = 'mew ex 232'
    #sch_phrase = 'aerodactyl v 180'
    item_loc = 'Australia only'
    ipg = 60
    dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)

    # regex
    dfls['mask_grade'] = (dfls['title'].str.contains('', na=False, case=False))
    dfls[['mask_grade','title']]

    # driver = get_chrome_driver(headless=False)
    # url = r'https://www.ebay.com.au/itm/187777556541?_skw=giratina+v+186%2F196&itmmeta=01KEEB37XCG43486XHR5GXVRHF&hash=item2bb86a203d:g:vG8AAeSwdVZpJjg1&itmprp=enc%3AAQAKAAAA8FkggFvd1GGDu0w3yXCmi1cGWJgSJWCKg7JEo77W2u9HcaUTer3y0L%2FdJDGnB197K8fDHhxzIIziwxB7z0g32qlCu4rEhN%2FzH7ad4ijZMQ%2F6PPh2tAqpHMxKZ4Ftgp%2FKh%2FR6ikYtMmR1%2FTE5w5MpSbtMNCbZqnGDFfO7Mj94cMqPlxgP0j7ordIyglZVHexwZVTvA5VL2DpFhMnuTDp14lJpOs9TblhGmyWPVGgqIA0jMhoLxjxInTX0wh24X1CXoZCqIJAS%2FBuyfXStD9tNI69m%2FCENHVGURERpouPsXW34NeRAeU1y0bzSgSXIwd6unQ%3D%3D%7Ctkp%3ABk9SR_T-jMvzZg'
    # img_urls = get_lst_imgs(url, driver)
    pass


