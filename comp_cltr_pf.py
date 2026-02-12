import warnings
warnings.filterwarnings('ignore')
import os.path
import pandas as pd
from pathlib import Path
import re
import string

from src.export_collectr_port import export_collectr_port
from src.common import get_chrome_driver, is_float, save2pkl
from src.get_ebayau_listing_data import get_ebayau_listing_data
from src.identify_lst_outliers import identify_lst_outliers

pattern_graded = r'(psa|cgc|bgs|beckett|ace|tag|ark)\s?([1-9](\.5)?|10)\b'
pattern_graded_company = r'(psa|cgc|bgs|beckett|ace|tag|ark)\s?'

def parse_search_phrase(sch_phrase):
    sch_phrase_meta = {}
    tmp_sch_phrase = sch_phrase

    re_search = re.search(pattern_graded, tmp_sch_phrase, re.IGNORECASE)
    if bool(re_search):
        pattern_found = re_search.group()
        sch_phrase_meta['graded_name'] = pattern_found
        sch_phrase_meta['graded_company'] = re.search(pattern_graded_company, pattern_found,
                                                             re.IGNORECASE).group().strip()
        sch_phrase_meta['graded_number'] = pattern_found.strip(sch_phrase_meta['graded_company']).strip()
        tmp_sch_phrase = tmp_sch_phrase.strip(pattern_found).strip()  # remove graded name

    # find card number
    if is_float(tmp_sch_phrase[-1]):  # card num at end
        card_num_str = tmp_sch_phrase.rsplit(maxsplit=1)[1].strip()
    elif is_float(tmp_sch_phrase[0]):  # card num at beginning
        card_num_str = tmp_sch_phrase.split(maxsplit=1)[0].strip()
    else:  # no card num provided
        card_num_str = ''
    card_num = card_num_str.split('/')[0].strip() if '/' in card_num_str else card_num_str
    sch_phrase_meta['card_num'] = card_num_str  # full card number
    sch_phrase_meta['card_num0'] = card_num  # only first half

    # infer card name
    card_name = tmp_sch_phrase.strip(card_num_str).strip()
    if 'graded_name' in sch_phrase_meta.keys():
        card_name = card_name.strip(sch_phrase_meta['graded_name']).strip()
    sch_phrase_meta['card_name'] = card_name
    return sch_phrase_meta


def filter_ebay_data(sch_phrase, dfls):
    rm_best_offer = True
    rm_outliers = True
    mtch_card_num = True
    rm_graded = True
    mtch_srch_phrase = True

    tmpdf = dfls.copy()
    sch_phrase_meta = parse_search_phrase(sch_phrase)

    # apply fitlers
    mask = tmpdf['title'] == tmpdf['title']
    if rm_best_offer:
        mask = mask & (tmpdf['auction_type'] != 'Best Offer')
    if mtch_card_num:
        # identify if graded card search
        if 'graded_name' in sch_phrase_meta.keys():
            pattern_found = sch_phrase_meta['graded_name']
            rm_graded = False
            graded_company = sch_phrase_meta['graded_company']
            graded_num = sch_phrase_meta['graded_number']
            tmp_pattern = rf"({graded_company})\s?({graded_num})\b"
            mask = mask & (tmpdf['title'].str.contains(tmp_pattern, na=False, case=False))  # match graded name

        # match card number
        card_num0 = sch_phrase_meta['card_num0']
        mask = mask & (tmpdf['title'].str.contains(f"{card_num0}", na=False, case=False))
    if rm_graded:
        mask = mask & (~tmpdf['title'].str.contains(pattern_graded, na=False, case=False))
    if mtch_srch_phrase:
        # must have name and card num in srch
        # remove punctuation first
        card_name = sch_phrase_meta['card_name']
        table = str.maketrans('', '', string.punctuation)
        card_name = card_name.translate(table)
        card_name_tokens = [c.strip() for c in card_name.split(' ')]

        # each token needs to be in the title
        # remove punctuation first
        tmpdf['title_stripped'] = tmpdf['title'].str.replace(r'[^\w\s]', '', regex=True)
        for token in card_name_tokens:
            mask = mask & (tmpdf['title_stripped'].str.contains(token, na=False, case=False))

        # match card number
        card_num0 = sch_phrase_meta['card_num0']
        mask = mask & (tmpdf['title'].str.contains(f"{card_num0}", na=False, case=False))
    if rm_outliers:
        tmpdf2 = tmpdf.copy()
        tmpdf2['include_lst_filters'] = mask
        tmpdf = identify_lst_outliers(tmpdf2) # outliers
        mask = mask & (~tmpdf['is_outlier'])

    # insert filter mask
    tmpdf['include_lst_filters'] = mask
    return tmpdf


def update_pf_ebay(pf_loc, pf_ebay_loc, pf_ebay_lsts_loc, update_lsts=True):
    # parameters
    item_loc = 'Australia only'
    ipg = 60 if item_loc=='Australia only' else 120
    hist_lens = {'1 week':7, '2 weeks':14,'3 weeks':21,'4 weeks':28, 'max':28*6}

    # load pf
    pf = pd.read_csv(pf_loc)
    pf_ebay = pd.read_csv(pf_ebay_loc) if os.path.isfile(pf_ebay_loc) else pf
    if 'price_mkt' not in pf_ebay.columns:
        for c in [f"price_ebay_median_{c}" for c in hist_lens.keys()] + ['price_mkt']:
            pf_ebay[c] = None

    # get ebay data - save as we go
    pf['name_str'] = pf['name'].str.split('(', n=1, expand=True)[0].str.strip()
    pf['itm_number_str'] = pf['itm_number'].fillna('').str.strip()
    pf['graded_str'] = pf['graded'].fillna('').str.strip()
    pf['sch_phrase'] = pf['name_str'] + ' ' + pf['itm_number_str'] + ' ' + pf['graded_str']
    pf['sch_phrase'] = pf['sch_phrase'].str.strip()

    driver = get_chrome_driver(headless=False, use_local=True, max_window=True)
    num_len = len(pf)
    ebay_lsts = pd.read_pickle(pf_ebay_lsts_loc) if os.path.isfile(pf_ebay_lsts_loc) else {}
    for ix, row in pf.iterrows():
        if pd.notnull(pf_ebay.loc[ix, 'price_mkt']):
            continue

        # ebay data
        sch_phrase = row['sch_phrase']
        print(f" -> {ix}/{num_len} - {sch_phrase}")

        sch_phrase_id = f"{sch_phrase}_{item_loc}"
        if (sch_phrase_id not in ebay_lsts.keys()) | update_lsts:
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)
            ebay_lsts[sch_phrase_id] = dfls
            if len(dfls)==0:
                pass
            save2pkl(ebay_lsts, pf_ebay_lsts_loc)
            #continue
        else:
            dfls = ebay_lsts[sch_phrase_id]

        # filter listings
        dfls_filtered = filter_ebay_data(sch_phrase, dfls)
        dfls_filtered_applied = dfls_filtered.loc[dfls_filtered['include_lst_filters']]

        # get mkt price
        today = pd.Timestamp.today().normalize()
        for hz_str in hist_lens.keys():
            hist_sdate = today - pd.Timedelta(days=hist_lens[hz_str])
            mask = dfls_filtered_applied['sold_date']>=hist_sdate
            dfls_h = dfls_filtered_applied.loc[mask]
            pf_ebay.loc[ix, f"price_ebay_median_{hz_str}"] = dfls_h['price'].median()

        # calc mkt price
        cols = [f"price_ebay_median_{c}" for c in hist_lens.keys() if c!='max']
        pf_ebay.loc[ix, 'price_mkt'] = pf_ebay.loc[ix, cols].max()

        # save
        pf_ebay.to_csv(pf_ebay_loc, index=False)

    # delete some cols
    cols2keep = ['name','set','rarity','itm_number','graded','currency','price_collectr']
    cols2keep = cols2keep + [f"price_ebay_median_{c}" for c in hist_lens.keys()] + ['price_mkt', 'sch_phrase']
    pf_ebay = pf_ebay[cols2keep]
    pcols = [f"price_ebay_median_{c}" for c in hist_lens.keys()] + ['price_mkt']
    pf_ebay[pcols] = pf_ebay[pcols].astype(float).round(2)

    # save
    pf_ebay.to_csv(pf_ebay_loc, index=False)
    driver.close()
    pass



if __name__ == '__main__':
    _export_collectr_pf = True
    _update_pf_ebay = True

    pf_loc = rf'{Path.cwd()}/saved_data/port_cltr.csv'
    pf_ebay_loc = rf'{Path.cwd()}/saved_data/port_cltr_ebay.csv'
    pf_ebay_lsts_loc = rf'{Path.cwd()}/saved_data/ebay_lsts.pkl'
    # 1) download collectr portfolio
    if _export_collectr_pf:
        driver = get_chrome_driver(headless=False, use_local=True, max_window=True)
        port_url = r'https://app.getcollectr.com/showcase/profile/24ba5413-66b8-4eb4-a5c3-fb93cd6480e0'
        export_collectr_port(port_url, pf_loc, driver)
        driver.close()
        pass

    # 2)
    if _update_pf_ebay:
        update_pf_ebay(pf_loc, pf_ebay_loc, pf_ebay_lsts_loc, update_lsts=False)
        pass

