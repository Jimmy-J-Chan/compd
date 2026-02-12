import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
from pathlib import Path

from src.common import encode_str, get_chrome_driver
from src.get_collectr_data import parse_all_itms

def check_pf_available(driver):
    wait = WebDriverWait(driver, 3)
    try:
        # if pf made available
        pf_xpath = "//h1[text()='Portfolio:']"
        flag_avail = wait.until(EC.element_to_be_clickable((By.XPATH, pf_xpath)))
    except:
        # no portfolio
        try:
            no_pf_xpath = "//h4[text()='No Results Found.'] | //p[text()='No cards found in this portfolio']"
            flag_avail = wait.until(EC.element_to_be_clickable((By.XPATH, no_pf_xpath)))
            raise Exception('No cards found in this portfolio')
        except:
            raise Exception('Unexpected Page Loaded')

def print_todo():
    print('##################################################')
    print('-> Have you changed the currency from USD to AUD?')
    print('-> Have you selected the portfolio to download?')
    print('##################################################')

    while True:
        flag_continue = input('-> Ready to continue? y/n')
        if flag_continue.lower() in ['y','yes']:
            return

def load_pf_all_itms(driver):
    # to bring window back up
    driver.maximize_window()
    time.sleep(2)

    # Get initial scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for page to load
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    pass

def get_current_ccy(driver):
    wait = WebDriverWait(driver, 2)
    try:
        ccy_xpath = r'/html/body/div[2]/div[1]/div/div/div[3]/div[1]/button[2]/p'
        ccy_button = wait.until(EC.element_to_be_clickable((By.XPATH, ccy_xpath)))
    except:
        ccy_xpath = r'/html/body/div[2]/div[1]/div/div/div[3]/div[2]/button/p'
        ccy_button = wait.until(EC.element_to_be_clickable((By.XPATH, ccy_xpath)))
    ccy = ccy_button.text.strip()
    return ccy

def get_selected_portfolio(driver):
    # Get the page source and hand it over to BeautifulSoup
    ccy = get_current_ccy(driver)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    all_itms = [c for c in soup.find_all(class_='h-full list-none')]
    if len(all_itms)==0:
        return {'error': 'no data'}
    else:
        df_all_itms = parse_all_itms(all_itms)
        df_all_itms['currency'] = ccy
        df_all_itms = df_all_itms.rename(columns={'itm_p':'price_collectr'})
    return df_all_itms

def export_collectr_port(port_url, save_loc, driver):
    # login into collectr
    driver.get(port_url)
    check_pf_available(driver)
    print_todo()
    load_pf_all_itms(driver)

    # download portfolio
    pf = get_selected_portfolio(driver)

    # save portfolio
    pf.to_csv(save_loc, index=False)
    pass


if __name__ == '__main__':
    save_loc = rf'{Path.cwd().parent}/saved_data/port_cltr.csv'
    driver = get_chrome_driver(headless=False, use_local=True, max_window=True)
    port_url = r'https://app.getcollectr.com/showcase/profile/24ba5413-66b8-4eb4-a5c3-fb93cd6480e0'
    export_collectr_port(port_url, save_loc, driver)