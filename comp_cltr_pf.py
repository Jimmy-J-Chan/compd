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
    card_name = tmp_sch_phrase.replace(card_num_str,'').strip()
    if 'graded_name' in sch_phrase_meta.keys():
        card_name = card_name.replace(sch_phrase_meta['graded_name'],'').strip()
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

def filter_by_ball_rarity(sch_phrase, dfls):
    # ball rarity
    tmp_pattern = r'(poke|master)\s?(ball)\b'
    mb_pattern = r'master\s?(ball)\b'
    pb_pattern = r'poke\s?(ball)\b'
    mb_search = re.search(mb_pattern, sch_phrase, re.IGNORECASE)
    pb_search = re.search(pb_pattern, sch_phrase, re.IGNORECASE)

    # search for ball pattern
    if bool(mb_search):
        ball_pattern = mb_pattern
    elif bool(pb_search):
        ball_pattern = pb_pattern
    else:
        return dfls

    # keep lsts with pattern
    mask = dfls['title'].str.contains(ball_pattern, na=False, case=False)
    dfls['include_lst_filters'] = mask & dfls['include_lst_filters']
    return dfls

def filter_by_promo_rarity(sch_phrase, dfls):

    # promo_stamp rarity
    tmp_pattern = r'(promo|stamp|stamped|svp)\b'
    promo_search = re.search(tmp_pattern, sch_phrase, re.IGNORECASE)

    # search for promo pattern
    if bool(promo_search):
        # keep promo only
        mask = dfls['title'].str.contains(tmp_pattern, na=False, case=False)
    else:
        # remove promos
        mask = ~dfls['title'].str.contains(tmp_pattern, na=False, case=False)

    # update
    # dfls['mask'] = mask
    # dfls[['title','mask','include_lst_filters']]
    dfls['include_lst_filters'] = mask & dfls['include_lst_filters']
    return dfls


def update_pf_ebay(pf_loc, pf_ebay_loc, pf_ebay_lsts_loc, update_lsts_only=True, detect_rarity=False, item_loc=None):
    # parameters
    today = pd.Timestamp.today().normalize()
    item_loc = 'Australia only' if item_loc is None else item_loc
    ipg = 60 if item_loc=='Australia only' else 240
    hist_lens = {'1 week':7, '2 weeks':14,'3 weeks':21,'4 weeks':28}#, 'max':28*6}

    # load pf
    pf = pd.read_csv(pf_loc)
    # pcols = [f"price_ebay_median_{c}" for c in hist_lens.keys()] + [f"price_ebay_max_{c}" for c in hist_lens.keys()]
    # pcols = [f"p_ebay_q75_{c.replace(' ', '').replace('weeks','w').replace('week','w').strip()}" for c in hist_lens.keys()]
    # if pcols[0] not in pf.columns:
    #     for c in pcols:
    #         pf[c] = None

    # get ebay data - save as we go
    #pf['name_str'] = pf['name'].str.split('(', n=1, expand=True)[0].str.strip()
    pf['name_str'] = pf['name'].str.replace('(','').str.replace(')','')
    for w in ['pattern','cosmos holo', '[',']','Alternate Full Art','Full Art','Secret','&']:
        pf['name_str'] = pf['name_str'].str.replace(w,'', case=False).str.strip()
    if detect_rarity:
        mask = pf['rarity']=='Promo'
        pf.loc[mask,'name_str'] = pf.loc[mask,'name_str'] + ' promo'
    mask = pf['set'].str.contains('celebrations', na=False, case=False)
    if mask.any():
        pf.loc[mask,'name_str'] = pf.loc[mask,'name_str'] + ' celebrations'

    pf['itm_number_str'] = pf['itm_number'].fillna('').str.strip()
    pf['graded_str'] = pf['graded'].fillna('').str.strip()
    pf['sch_phrase'] = pf['name_str'] + ' ' + pf['itm_number_str'] + ' ' + pf['graded_str']
    pf['sch_phrase'] = pf['sch_phrase'].str.strip()

    driver = get_chrome_driver(headless=False, use_local=True, max_window=True)
    num_len = len(pf)
    pf_ebay = pf.copy()

    ebay_lsts = pd.read_pickle(pf_ebay_lsts_loc) if os.path.isfile(pf_ebay_lsts_loc) else {}
    for ix, row in pf[:].iterrows(): # 2:14 - 2:33 = 19mins

        # ebay data
        sch_phrase = row['sch_phrase']
        print(f" -> {ix}/{num_len} - {sch_phrase}")
        sch_phrase_id = f"{sch_phrase}_{item_loc}"

        # update previous check
        update_cache = False
        if sch_phrase_id in ebay_lsts.keys():
            update_dt = ebay_lsts[sch_phrase_id]['update_dt'].iloc[0]
            if update_dt < today:
                update_cache = True

        if (sch_phrase_id not in ebay_lsts.keys()) | update_lsts_only | update_cache:
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)
            dfls['update_dt'] = today
            ebay_lsts[sch_phrase_id] = dfls
            if len(dfls)==0:
                pass
            save2pkl(ebay_lsts, pf_ebay_lsts_loc)

            if update_lsts_only:
                continue
        else:
            dfls = ebay_lsts[sch_phrase_id]

        # filter listings
        dfls_filtered = filter_ebay_data(sch_phrase, dfls)
        if detect_rarity:
            dfls_filtered = filter_by_ball_rarity(sch_phrase, dfls_filtered)
            dfls_filtered = filter_by_promo_rarity(sch_phrase, dfls_filtered)
        dfls_filtered_applied = dfls_filtered.loc[dfls_filtered['include_lst_filters']]

        # calc median prices
        today = pd.Timestamp.today().normalize()
        for hz_str in hist_lens.keys():
            hist_sdate = today - pd.Timedelta(days=hist_lens[hz_str])
            mask = dfls_filtered_applied['sold_date']>=hist_sdate
            dfls_h = dfls_filtered_applied.loc[mask]
            hz_str2 = hz_str.replace(' ', '').replace('weeks','w').replace('week','w').strip()
            pf_ebay.loc[ix, f"p_ebay_q75_{hz_str2}"] = dfls_h['price'].quantile(0.75)
            pf_ebay.loc[ix, f"p_ebay_median_{hz_str}"] = dfls_h['price'].median()
            # pf_ebay.loc[ix, f"price_ebay_max_{hz_str}"] = dfls_h['price'].max()

    # # calc some prices
    q75_cols = [c for c in pf_ebay.columns if c.startswith('p_ebay_q75_')]
    median_cols = [c for c in pf_ebay.columns if c.startswith('p_ebay_median_')]
    pf_ebay['p_ebay_q75_high'] = pf_ebay[q75_cols].max(axis=1)
    pf_ebay['p_ebay_median_high'] = pf_ebay[median_cols].max(axis=1)

    if update_lsts_only:
        return

    # delete some cols
    pcols = median_cols + ['p_ebay_median_high','p_ebay_q75_high','price_collectr']
    cols2keep = ['name','set','rarity','itm_number','graded','currency','qty']
    cols2keep = cols2keep + pcols + ['sch_phrase']
    pf_ebay = pf_ebay[cols2keep]
    pf_ebay[pcols] = pf_ebay[pcols].astype(float).round(2)

    # pf totals
    mask = pf_ebay['p_ebay_q75_high'].isnull()
    pf_ebay.loc[mask, 'p_ebay_q75_high'] = pf_ebay.loc[mask, 'price_collectr']
    #pf_ebay['pf_q75_total'] = (pf_ebay['qty'] * pf_ebay['p_ebay_q75_high']).sum().round(2)
    #pf_ebay['pf_cltr_total'] = (pf_ebay['qty'] * pf_ebay['price_collectr']).sum().round(2)

    # save
    # pf_ebay.sort_values('p_ebay_median_high', ascending=False)
    pf_ebay.to_csv(pf_ebay_loc, index=False)
    driver.close()
    pass

def update_vc():
    params = {'Australia only':{'fn_sfx': 'vc',
                                'detect_rarity': False,
                                'item_loc': 'Australia only',
                                },
              'Worldwide': {'fn_sfx': 'wrld',
                            'item_loc': 'Worldwide',
                            'detect_rarity': False,
                            }
              }


    pfs = ['Australia only','Worldwide']
    pf_loc = rf'{Path.cwd()}/saved_data/port_cltr.csv' # collectr port

    driver = get_chrome_driver(headless=False, use_local=True, max_window=True)
    port_url = r'https://app.getcollectr.com/showcase/profile/24ba5413-66b8-4eb4-a5c3-fb93cd6480e0'
    export_collectr_port(port_url, pf_loc, driver)
    driver.close()

    for pf in pfs:
        fn_sfx = params[pf]['fn_sfx']
        item_loc = params[pf]['item_loc']
        detect_rarity = params[pf]['detect_rarity']

        fn_sfx = f"_{fn_sfx}" if ((not fn_sfx.startswith('_')) and (len(fn_sfx) > 0)) else fn_sfx
        pf_ebay_loc = rf'{Path.cwd()}/saved_data/port_cltr_ebay{fn_sfx}.csv'  # collectr + ebay data
        pf_ebay_lsts_loc = rf'{Path.cwd()}/saved_data/ebay_lsts{fn_sfx}.pkl'  # store raw ebay listings

        update_pf_ebay(pf_loc, pf_ebay_loc, pf_ebay_lsts_loc,
                       update_lsts_only=False, detect_rarity=detect_rarity, item_loc=item_loc)
    pass


if __name__ == '__main__':
    # update_vc()

    _export_collectr_pf = True
    _update_pf_ebay = True

    # save locs - AU
    fn_sfx = 'vc_pc'
    item_loc = 'Australia only'
    detect_rarity = False

    # # save locs - Wrld
    # fn_sfx = 'wrld'
    # item_loc = 'Worldwide'
    # detect_rarity = False

    # # save locs - pris
    # fn_sfx = 'PRE'
    # detect_rarity = True
    #
    # # save locs - bbwf
    # fn_sfx = 'BBWF'
    # detect_rarity = True

    fn_sfx = f"_{fn_sfx}" if ((not fn_sfx.startswith('_')) and (len(fn_sfx)>0)) else fn_sfx
    pf_loc = rf'{Path.cwd()}/saved_data/port_cltr{fn_sfx}.csv' # collectr port
    pf_ebay_loc = rf'{Path.cwd()}/saved_data/port_cltr_ebay{fn_sfx}.csv' # collectr + ebay data
    pf_ebay_lsts_loc = rf'{Path.cwd()}/saved_data/ebay_lsts{fn_sfx}.pkl' # store raw ebay listings

    # 1) download collectr portfolio
    if _export_collectr_pf:
        driver = get_chrome_driver(headless=False, use_local=True, max_window=True)
        port_url = r'https://app.getcollectr.com/showcase/profile/24ba5413-66b8-4eb4-a5c3-fb93cd6480e0'
        export_collectr_port(port_url, pf_loc, driver)
        driver.close()
        pass

    # 2)
    if _update_pf_ebay:
        update_pf_ebay(pf_loc, pf_ebay_loc, pf_ebay_lsts_loc,
                       update_lsts_only=False, detect_rarity=detect_rarity, item_loc=item_loc)
    pass

