import streamlit as st
import pandas as pd
import altair as alt
import re
import os
import string

from conf.config import ss_g, hist2days, loc_map
from src.common import (set_scroll2top_button, set_chrome_driver, write_style_str,
                        is_float)
from src.get_ebayau_listing_data import get_ebayau_listing_data, get_lst_imgs
from src.get_collectr_data import get_collectr_data
from src.get_fx_rate import get_audusd_rate
from src.identify_lst_outliers import identify_lst_outliers
from compd_desktop import (set_session_state_groups, set_sidebar_elements, set_tabs,
                           show_more_listing_imgs, show_pf_itm_listing)

# page settings
st.set_page_config(page_title="Compd",
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )


def set_tsearch():
    def _set_stats_board():
        contr_stats = st.container(border=True)
        st.session_state.contr_stats = contr_stats
        contr_stats.write('#### Selected listings:')

    def _set_pchart_container():
        contr_pchart = st.container(border=True)
        st.session_state.contr_pchart = contr_pchart

    def _update_stats_board():
        # df: selected listings, match history param
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst'] & _dfls['include_lst_filters']]
        num_lsts = len(_dfls)
        num_lsts_total = len(st.session_state['itms'][itm_id]['dfls'])
        if num_lsts > 0:
            stats = {'date_range_str': f"Date range: **{_dfls['sold_date'].min():%d %b %Y} - {_dfls['sold_date'].max():%d %b %Y}**",
                     'listings_str': f"Listings shown: **{num_lsts}/{num_lsts_total}**",
                     'price_range_str': f"Price range: **\${_dfls['price'].min()} - \${_dfls['price'].max()}**",
                     #'last_sold_str': f"Last Sold: {}",
                     'mean_str': f"Mean: **${_dfls['price'].mean():.2f}**",
                     'median_str': f"Median: **${_dfls['price'].median():.2f}**",
                     'dr_start': dfls['sold_date'].min(),
                     'dr_end': dfls['sold_date'].max(),
                     'num_listings': num_lsts,
                     'price_min': _dfls['price'].min(),
                     'price_max': _dfls['price'].max(),
                     'mean': _dfls['price'].mean(),
                     'median': _dfls['price'].median(),
                     }

            contr_stats = st.session_state.contr_stats
            contr_stats.write(stats['date_range_str'])
            contr_stats.write(stats['listings_str'])
            contr_stats.write(stats['price_range_str'])
            contr_stats.write(stats['mean_str'])
            contr_stats.write(stats['median_str'])

            if st.session_state['sb']['get_collectr_p']:
                cltr_d = st.session_state['itms'][itm_id]['collectr']
                if (len(cltr_d.keys())>0) & ('error' not in cltr_d.keys()):
                    cltr_p = st.session_state['itms'][itm_id]['collectr']['itm_p']
                    cltr_url = st.session_state['itms'][itm_id]['collectr']['sch_phrase_url']
                    write_style_str(parent_obj=contr_stats, str_out=f'Collectr: ${cltr_p:.2f}', font_w='bold', color="#000000",
                                    hyperlink=cltr_url)
                else:
                    contr_stats.write(f'Collectr: N/A')

            # add price
            contr_stats_p = contr_stats.container(horizontal=True, gap='small', width='content',
                                                  vertical_alignment="top")
            write_style_str(parent_obj=contr_stats_p, str_out='Price: ')
            price_input = contr_stats_p.text_input(label='', label_visibility='collapsed',
                                                   placeholder=f"{stats['mean']:.2f}",
                                                   key="price_input", width=100)
            # set default value
            if len(price_input)==0:
                price_input = stats['mean']

            try:
                price_input = float(price_input)
                stats['price_input'] = price_input

                # save to pf button
                pf_name = st.session_state['sb']['pf_name']
                if contr_stats.button(f'Add to Portfolio'):
                    if itm_id not in st.session_state.pf['itms'].keys():
                        st.session_state.pf['itms'][itm_id] = {}
                    st.session_state.pf['itms'][itm_id]['dfls'] = _dfls
                    st.session_state.pf['itms'][itm_id]['stats'] = stats
                    st.session_state.pf['itms'][itm_id]['pf_name'] = pf_name
                    st.toast(f"Saved to Portfolio: {pf_name}", icon="✔️")

            except ValueError:
                write_style_str(parent_obj=contr_stats_p, str_out='Enter valid price!',
                                color='red', font_w='bold')

    def _update_price_chart():
        # df: selected listings, match history param
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst'] & _dfls['include_lst_filters']]

        contr_pchart = st.session_state.contr_pchart
        if len(_dfls)>1:
            # calc median by date
            price_median = _dfls.groupby('sold_date')['price'].median()
            _dfls['price_median'] = _dfls['sold_date'].map(price_median)

            x_col_name = 'sold_date'
            y_scatter_col_name = 'price'
            y_line_col_name = 'price_median'
            x_axis_min = _dfls[x_col_name].min() - pd.Timedelta(days=1)
            x_axis_max = _dfls[x_col_name].max() + pd.Timedelta(days=1)
            y_axis_min = int(_dfls[y_scatter_col_name].min() * 0.9)
            y_axis_max = int(_dfls[y_scatter_col_name].max() * 1.1)

            x_axis = alt.X(f'{x_col_name}:T', scale=alt.Scale(domain=[x_axis_min, x_axis_max]), title=None)#, axis=alt.Axis(grid=False))
            y_scatter_axis = alt.Y(f'{y_scatter_col_name}:Q', scale=alt.Scale(domain=[y_axis_min, y_axis_max]), title=None, axis=alt.Axis(grid=False))
            y_line_axis = alt.Y(f'{y_line_col_name}:Q', scale=alt.Scale(domain=[y_axis_min, y_axis_max]), title=None, axis=alt.Axis(grid=False))

            line = alt.Chart(_dfls).mark_line(color='blue', size=2,
                                              opacity=0.5,).encode(x=x_axis, y=y_line_axis)
            scatter = alt.Chart(_dfls).mark_point(color='red', size=200,
                                                  filled=False, opacity=0.5,
                                                  strokeWidth=2).encode(x=x_axis, y=y_scatter_axis)
            contr_pchart.altair_chart(scatter + line, use_container_width=True, theme=None)
        else:
            write_style_str(parent_obj=contr_pchart,
                            str_out="Select more listings to generate price chart",
                            color="red", font_size="1em", font_w='bold')

    def _parse_search_phrase():
        tmp_sch_phrase = sch_phrase

        # identify if graded card search
        if 'graded_name' in st.session_state['sb'].keys():
            del st.session_state['sb']['graded_name']
            del st.session_state['sb']['graded_company']
            del st.session_state['sb']['graded_number']
        pattern_graded = st.session_state['sb']['pattern_graded']
        pattern_graded_company = st.session_state['sb']['pattern_graded_company']
        re_search = re.search(pattern_graded, tmp_sch_phrase, re.IGNORECASE)
        if bool(re_search):
            pattern_found = re_search.group()
            st.session_state['sb']['graded_name'] = pattern_found
            st.session_state['sb']['graded_company'] = re.search(pattern_graded_company, pattern_found, re.IGNORECASE).group().strip()
            st.session_state['sb']['graded_number'] = pattern_found.strip(st.session_state['sb']['graded_company']).strip()
            tmp_sch_phrase = tmp_sch_phrase.strip(pattern_found).strip() # remove graded name

        # find card number
        if is_float(tmp_sch_phrase[-1]):  # card num at end
            card_num_str = tmp_sch_phrase.rsplit(maxsplit=1)[1].strip()
        elif is_float(tmp_sch_phrase[0]):  # card num at beginning
            card_num_str = tmp_sch_phrase.split(maxsplit=1)[0].strip()
        else:  # no card num provided
            card_num_str = ''
        card_num = card_num_str.split('/')[0].strip() if '/' in card_num_str else card_num_str
        st.session_state['sb']['card_num'] = card_num_str # full card number
        st.session_state['sb']['card_num0'] = card_num # only first half

        # infer card name
        card_name = tmp_sch_phrase.strip(card_num_str).strip()
        if 'graded_name' in st.session_state.keys():
            card_name = card_name.strip(st.session_state['sb']['graded_name']).strip()
        st.session_state['sb']['card_name'] = card_name

    ####################################################################################################################

    with st.session_state['tabs']['search']:
        # search bar
        sch_phrase = st.text_input(label='',
                                   label_visibility='collapsed',
                                   placeholder='Enter card name and number',
                                   key='sch_phrase_in'
                                   )
        sch_phrase = sch_phrase.strip()

        # manage search bar input
        if len(sch_phrase) == 0:
            # show nothing
            return
        elif len(sch_phrase.split(' '))<2:
            st.write('### Invalid search: enter item name and number')
            return

        # get listing data
        item_loc = st.session_state['sb']['item_loc']
        itm_id = f"{sch_phrase}_{loc_map[item_loc]}"

        driver = st.session_state.chrome_driver
        if itm_id not in st.session_state['itms'].keys():
            st.session_state['itms'][itm_id] = {}
            ipg = st.session_state['sb']['ipg']
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)
            dfls['include_lst'] = True # mask for btns
            dfls['include_lst_filters'] = False # mask for sidebar filters
            st.session_state['itms'][itm_id]['dfls'] = dfls.copy()
            st.session_state['itms'][itm_id]['sch_phrase'] = sch_phrase
            st.session_state['itms'][itm_id]['item_loc'] = item_loc
        else:
            dfls = st.session_state['itms'][itm_id]['dfls'].copy()

        # if no data returned
        if len(dfls)==0:
            st.write(f'### No listings returned for: {sch_phrase} - {loc_map[item_loc]}')
            return

        # get collectr price
        if st.session_state['sb']['get_collectr_p']:
            # get audusd rate t-1
            if 'audusd' not in st.session_state.keys():
                st.session_state['audusd'] = get_audusd_rate()

            if 'collectr' not in st.session_state['itms'][itm_id].keys():
                cltr_data = get_collectr_data(sch_phrase, driver)
                st.session_state['itms'][itm_id]['collectr'] = cltr_data

                # convert usd price to aud
                if 'itm_p' in cltr_data.keys():
                    audusd = st.session_state['audusd']
                    itm_p = st.session_state['itms'][itm_id]['collectr']['itm_p']
                    st.session_state['itms'][itm_id]['collectr']['itm_p'] = itm_p/audusd

        # pattern to identify graded cards
        st.session_state['sb']['pattern_graded'] = r'(psa|cgc|bgs|beckett|ace|tag|ark)\s?([1-9](\.5)?|10)\b'
        st.session_state['sb']['pattern_graded_company'] = r'(psa|cgc|bgs|beckett|ace|tag|ark)\s?'

        # parse the search phrase
        _parse_search_phrase()

        # prep the data to be displayed
        pattern_graded = st.session_state['sb']['pattern_graded']
        mask = dfls['sold_date'] >= st.session_state['sb']['hist_sdate']
        if st.session_state['sb']['rm_best_offer']:  # remove best offers
            mask = mask & (dfls['auction_type']!='Best Offer')
        if st.session_state['sb']['show_sltd_lsts']: # show selected listings only
            mask = mask & (dfls['include_lst'])
        if st.session_state['sb']['mtch_card_num']:
            # identify if graded card search
            if 'graded_name' in st.session_state['sb'].keys():
                pattern_found = st.session_state['sb']['graded_name']
                st.session_state['sb']['rm_graded'] = False
                graded_company = st.session_state['sb']['graded_company']
                graded_num = st.session_state['sb']['graded_number']
                tmp_pattern = rf"({graded_company})\s?({graded_num})\b"
                mask = mask & (dfls['title'].str.contains(tmp_pattern, na=False, case=False)) # match graded name

            # match card number
            card_num0 = st.session_state['sb']['card_num0']
            mask = mask & (dfls['title'].str.contains(f"{card_num0}", na=False, case=False))
        if st.session_state['sb']['rm_graded']:
            mask = mask & (~dfls['title'].str.contains(pattern_graded, na=False, case=False))
        if st.session_state['sb']['mtch_srch_phrase']:
            # must have name and card num in srch
            # remove punctuation first
            card_name = st.session_state['sb']['card_name']
            table = str.maketrans('', '', string.punctuation)
            card_name = card_name.translate(table)
            card_name_tokens = [c.strip() for c in card_name.split(' ')]

            # each token needs to be in the title
            # remove punctuation first
            dfls['title_stripped'] = dfls['title'].str.replace(r'[^\w\s]', '', regex=True)
            for token in card_name_tokens:
                mask = mask & (dfls['title_stripped'].str.contains(token, na=False, case=False))

            # match card number
            card_num0 = st.session_state['sb']['card_num0']
            mask = mask & (dfls['title'].str.contains(f"{card_num0}", na=False, case=False))
        if st.session_state['sb']['rm_outliers']:
            # identify and remove outliers
            dfls['include_lst_filters'] = mask
            dfls = identify_lst_outliers(dfls)
            mask = mask & (~dfls['is_outlier'])

        # update mask filters
        dfls['include_lst_filters'] = mask
        #st.write(dfls)

        # update filter mask
        st.session_state['itms'][itm_id]['dfls']['include_lst_filters'] = dfls['include_lst_filters']
        dfls = dfls.loc[mask] # lsts to display

        # if no data returned
        if len(dfls)==0:
            st.write(f'### No listings available for: {sch_phrase} - {loc_map[item_loc]}')
            return

        # set some data containers
        if st.session_state['sb']['show_pchart']: # price chart
            _set_pchart_container()
        _set_stats_board() # add container to show price stats

        # display parameters
        c2_img_size = 140

        # display data
        #dfls = dfls.head(5)
        for ix, lst in dfls.iterrows():
            # container - write horizontally
            contr = st.container(border=True)
            contr_1 = contr.container(horizontal=True,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap='small') # select, image

            # select button
            c1_key = f"{itm_id}_{ix}_c1"
            _button_state = contr_1.checkbox(label='',
                                            label_visibility='collapsed',
                                            key=c1_key,
                                            value=lst['include_lst'])
            st.session_state['itms'][itm_id]['dfls'].loc[ix, 'include_lst'] = _button_state # updates on the fly

            # show img0
            contr_1.image(f"{lst['img_url0']}/s-l{c2_img_size}.webp", width='content')

            # write vertically now
            contr_2 = contr_1.container(horizontal=False,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap="small")

            # details
            p = lst['price']
            p_str = f"{lst['price_str']}".replace('$',' ') if pd.isnull(p) else f"AU ${lst['price']}"
            write_style_str(parent_obj=contr_2, str_out=f"Sold  {lst['sold_date']:%d %b %Y}", color="#7D615E", font_size="1em")
            write_style_str(parent_obj=contr_2, str_out=lst['title'], color="#000000", font_size="1em", hyperlink=lst['sold_url'])
            strike_thr = True if lst['auction_type']=='Best Offer' else False
            write_style_str(parent_obj=contr_2, str_out=p_str, color="#7D615E", font_size="1.5em", font_w='bold', strike_through=strike_thr)
            write_style_str(parent_obj=contr_2, str_out=lst['auction_type'])
            write_style_str(parent_obj=contr_2, str_out=f"{lst['from_ctry_str']}", color="#7D615E", font_size="1em")

            # # show more imgs
            # c2_key = f"{itm_id}_{ix}_c2"
            # if contr_2.button('show more images', key=c2_key, width='content'):
            #     show_more_listing_imgs(lst['sold_url'])

            # delete some keys
            delattr(st.session_state, c1_key)
            #delattr(st.session_state, c2_key)

        # update containers above
        if st.session_state['sb']['show_pchart']:
            _update_price_chart()
        _update_stats_board()
        #st.write(st.session_state['itms'][itm_id]['dfls'])


    pass

def set_tport():
    def _set_portfolio_board():
        contr_pf = st.container(border=True)
        st.session_state.contr_pf = contr_pf
        contr_pf.write(f"#### Portfolio: {st.session_state['sb']['pf_name']}")

    def _update_portfolio_board():
        dfpf = st.session_state.pf['dfpf']
        dfpf = dfpf.loc[dfpf['pf_name']==pf_name]
        if dfpf['include_itm'].sum()>0:
            contr_pf = st.session_state.contr_pf
            total = (dfpf['price_input']*dfpf['include_itm']).sum()
            contr_pf.write(f"Total: **${total:.2f}**")

            c11 = contr_pf.container(horizontal=True)
            for pct in pcts_c1:
                _str = f"{int(pct*100)}%"
                c11.write(f"{_str}: **${total*pct:.2f}**")

            c22 = contr_pf.container(horizontal=True)
            for pct in pcts_c2:
                _str = f"{int(pct*100)}%"
                c22.write(f"{_str}: **${total*pct:.2f}**")
        pass

    def _create_dfpf():
        dfpf = [pd.Series(st.session_state.pf['itms'][itm_id]['stats']).to_frame(itm_id) for itm_id in itm_ids]
        dfpf = pd.concat(dfpf, axis=1).T

        # add corresponding pf_name
        pf_name_map = {itm_id: st.session_state.pf['itms'][itm_id]['pf_name'] for itm_id in itm_ids}
        dfpf['pf_name'] = dfpf.index.map(pf_name_map)

        cols = ['include_itm']#,'include_trde'] #, 'include_trde_you', 'include_trde_them']
        for col in cols:
            dfpf[col] = True
        return dfpf

    def save_btns_selected():
        mask = st.session_state.pf['dfpf']['pf_name']==pf_name
        st.session_state.pf['dfpf'].loc[mask, 'include_trde'] = st.session_state.pf['dfpf'].loc[mask,'include_itm'].copy()
        pass
    ####################################################################################################################

    # include_itm, , num items, pcts - 90,80,75
    # display portfolio - use most recent lst as photo
    pcts_c1 = [0.9, 0.80, 0.70]
    pcts_c2 = [0.85, 0.75, 0.6]

    # so no error at the beginning
    itm_ids = st.session_state.pf['itms'].keys()
    if len(itm_ids)==0:
        return

    # dfpf - itm_id, mean, median,
    if 'dfpf' not in st.session_state.pf.keys():
        #st.write('no dfpf detected')
        dfpf = _create_dfpf()
        st.session_state.pf['dfpf'] = dfpf
    else:
        dfpf_c = st.session_state.pf['dfpf']
        dfpf_c_idx = dfpf_c.index
        itm_name_diff = [c for c in itm_ids if c not in dfpf_c_idx]
        p_diff = [c for c in dfpf_c_idx if (dfpf_c.loc[c,'price_input']!=st.session_state.pf['itms'][c]['stats']['price_input'])]
        if (len(itm_name_diff)>0) | (len(p_diff)>0):
            #st.write('dfpf exist - diff detected')
            dfpf = _create_dfpf()
            st.session_state.pf['dfpf'] = dfpf
        else:
            #st.write('no diff detected')
            dfpf = st.session_state.pf['dfpf']


    tb_p = st.session_state['tabs']['portfolio']
    with tb_p:
        _set_portfolio_board()

        # filter by portfolio name
        pf_name = st.session_state['sb']['pf_name']
        dfpf = dfpf.loc[dfpf['pf_name']==pf_name]

        # display itms in pf
        for itm_id, row in dfpf.iterrows():
            stats = st.session_state.pf['itms'][itm_id]['stats']
            dfls = st.session_state.pf['itms'][itm_id]['dfls']

            # container - write horizontally
            contr = st.container(border=True)
            contr_1 = contr.container(horizontal=True,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap='small')

            # select button
            pf_c1_key = f"pf_{itm_id}_c1"
            value = st.session_state.pf['dfpf'].loc[itm_id, 'include_itm']
            _button_state = contr_1.checkbox(label='', label_visibility='collapsed', key=pf_c1_key, value=value)
            st.session_state.pf['dfpf'].loc[itm_id, 'include_itm'] = _button_state

            # use first image from dfls
            img_size = '140'
            contr_1.image(f"{dfls['img_url0'].iloc[0]}/s-l{img_size}.webp")

            # write vertically now
            contr_2 = contr_1.container(horizontal=False,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap="small")

            sch_phrase = st.session_state['itms'][itm_id]['sch_phrase']
            item_loc = st.session_state['itms'][itm_id]['item_loc']
            contr_2.write(f"{sch_phrase}")
            contr_2.write(f"${row['price_input']:.2f}")
            contr_2.write(f"{item_loc}")

            # compd itm info
            pf_c3_key = f"pf_{itm_id}_c3"
            if contr_2.button('Show Listings', key=pf_c3_key):
                show_pf_itm_listing(itm_id)

            # delete some keys
            delattr(st.session_state, pf_c1_key)
            delattr(st.session_state, pf_c3_key)

        # update container above
        _update_portfolio_board()
    pass

def set_ttrade():
    # area to split comps into two pf: you, them
    # gives you the cash/trade value difference after pct

    def _set_trade_board():
        contr_trde = st.container(border=True)
        st.session_state.contr_trde = contr_trde
        contr_trde.write('#### Trade Analyser')

        # set trade percentage
        contr_trde_pct = contr_trde.container(horizontal=True, gap='small', width='content',
                                              vertical_alignment="top")
        write_style_str(parent_obj=contr_trde_pct, str_out='Trade (%): ')
        trade_pct = contr_trde_pct.number_input(label='', min_value=0, max_value=100,
                                                value=80, step=5, width=130, label_visibility='collapsed',)

        # set cash percentage
        contr_cash_pct = contr_trde.container(horizontal=True, gap='small', width='content',
                                              vertical_alignment="top")
        write_style_str(parent_obj=contr_cash_pct, str_out='Cash (%): ')
        cash_pct = contr_cash_pct.number_input(label='', min_value=0, max_value=100,
                                                value=70, step=5, width=130, label_visibility='collapsed',)

        # print balances
        contr_trde.write('#### Totals')
        dfpf = st.session_state.pf['dfpf']
        total_map = {}
        for pfn in pf_names:
            trade_pct_pfn = trade_pct/100 if pfn=='You' else 1
            tmp_dfpf = dfpf.loc[dfpf['pf_name']==pfn]
            total = (tmp_dfpf['price_input']*tmp_dfpf['include_itm']).sum()
            total_pct = total * trade_pct_pfn
            total_map[pfn] = total_pct

            _str = f"{pfn}:  **\${total_pct:.2f}**"
            _str = _str if pfn=='Me' else f"{_str} -- [**{trade_pct}\%** of **\${total:.2f}**]"
            contr_trde.write(_str)

        t_me = total_map['Me']
        t_you = total_map['You']
        cash_bal = abs(t_me - t_you)
        contr_trde.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
        if t_me > t_you:
            contr_trde.write(f"Balance: **They pay you ${cash_bal:.2f}**")
        elif t_you > t_me:
            cash_out = (cash_bal/trade_pct)*cash_pct
            contr_trde.write(f"Remaining Trade Credit: **${cash_bal:.2f}**")
            contr_trde.write(f"OR Cash Out: **\${cash_out:.2f}** -- [\${cash_bal:.2f} / {trade_pct:.0f}\% * {cash_pct:.0f}\%]")
        elif (cash_bal<=1) & (cash_bal >= -1):
            contr_trde.write(f"Balance: **Fair Trade**")

    ####################################################################################################################
    # so no error at the beginning
    # this should autocalc without clicking on the pf tab
    if 'dfpf' not in st.session_state.pf.keys():
        return

    pf_names = st.session_state['sb']['pf_names']
    pf_name = st.session_state['sb']['pf_name']
    tb_p = st.session_state['tabs']['trade']
    with tb_p:
        _set_trade_board()
    pass



def compd_mobile():
    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    set_tport()
    set_ttrade()
    pass


if __name__ == '__main__':
    compd_mobile()
    pass