import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup

from src.common import encode_str, get_chrome_driver


def parse_all_itms(all_itms):
    df = []
    for itm in all_itms:
        itmd = {}
        l1 = itm.find('div', recursive=False)
        l1div = l1.find_all('div', recursive=False)
        itm_meta = l1div[1].find_all('div',recursive=False)[1].find_all('span')
        itm_p = l1div[2].find_all('div',recursive=False)

        itmd['name'] = l1.find('span').text.strip()
        itmd['set'] = l1div[1].find_all('div',recursive=False)[0].text.strip()
        itmd['rarity'] = itm_meta[0].text.strip()
        itmd['itm_number'] = itm_meta[2].text.strip()
        itmd['itm_p_str'] = itm_p[0].find('div').find('span').text
        itmd['itm_p'] = float(itmd['itm_p_str'].strip('A$').strip())
        img_url = l1div[0].find('img', recursive=False).attrs['src']
        product_id = img_url.split('?')[0].strip('https://public.getcollectr.com/public-assets/products/product_.jpg').strip()
        itmd['itm_url'] = f"https://app.getcollectr.com/explore/product/{product_id}"
        df.append(itmd)
    df = pd.DataFrame(df)
    return df


def get_collectr_data(sch_phrase, _driver):
    if len(sch_phrase)==0:
        return {}

    driver = _driver
    base_url = r"https://app.getcollectr.com/?query={}"
    enc_str = encode_str(sch_phrase)
    url = base_url.format(enc_str)
    driver.get(url)

    # Wait a few seconds for JavaScript to load the price data
    time.sleep(2)

    # check currency
    wait = WebDriverWait(driver, 2)
    xpath = "(//button[contains(., 'USD') or contains(., 'AUD')])[2]"
    ccy_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    if ccy_button.text != 'USD':
        return {'error': 'USD not selected'}

    # wait = WebDriverWait(driver, 2)
    # try:
    #     xpath = "(//button[contains(., 'USD') or contains(., 'AUD')])[2]"
    #     ccy_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    #     ccy_button.click()
    #     #time.sleep(1)
    # except:
    #     try:
    #         xpath = "//button[contains(., 'USD') or contains(., 'AUD')]"
    #         ccy_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    #         ccy_button.click()
    #         #time.sleep(1)
    #     except:
    #         return {'error':'USD or AUD not selected'}
    #
    # if ccy_button.text=='USD':
    #     try:
    #         # search for any element containing the text 'AUD' that is clickable
    #         aud_selection_xpath = "//div[text()='AUD'] | //span[text()='AUD'] | //p[text()='AUD']"
    #         aud_button = wait.until(EC.element_to_be_clickable((By.XPATH, aud_selection_xpath)))
    #         aud_button.click()
    #         #time.sleep(1)
    #     except:
    #         return {'error': 'could not select AUD'}

    # Get the page source and hand it over to BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    all_itms = [c for c in soup.find_all(class_='h-full list-none')]
    if len(all_itms)==0:
        return {'error': 'no data'}
    else:
        all_itms = all_itms[:1]
        df_all_itms = parse_all_itms(all_itms)
        df_all_itms['ccy'] = ccy_button.text

        # return first itm
        cltr_d = df_all_itms.loc[0].to_dict()
        cltr_d['sch_phrase_url'] = url
        return cltr_d


if __name__ == '__main__':
    driver = get_chrome_driver(headless=True, use_local=True, max_window=True)
    sch_phrase = 'mew ex 232'
    cltr_d = get_collectr_data(sch_phrase, driver)
    pass