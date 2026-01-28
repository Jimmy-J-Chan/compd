import os

import streamlit as st
import pandas as pd
import altair as alt

from conf.config import ss_g, hist2days, loc_map
from src.common import set_scroll2top_button, set_chrome_driver, write_style_str, save2pkl, load_pkl
from src.get_ebayau_listing_data import get_ebayau_listing_data, get_lst_imgs

# page settings
st.set_page_config(page_title="Compd",
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )

def set_session_state_groups():
    for g in ss_g:
        if g not in st.session_state.keys():
            st.session_state[g] = {}
            if g=='pf':
                st.session_state.pf['itms'] = {}

def reset_session_state_params_data():
    # only reset itms and pf, keep sb params and tabs
    if 'sch_phrase_in' in st.session_state.keys():
        st.session_state.sch_phrase_in = ''
    for g in ['itms', 'pf']:
        st.session_state[g] = {}
        if g == 'pf':
            st.session_state.pf['itms'] = {}

def deselect_lstings():
    if ('itm_id_in' in st.session_state.keys()) & ('deselect_btn' in st.session_state.keys()):
        if st.session_state.deselect_btn:
            itm_id = st.session_state['itm_id_in']
            st.session_state['itms'][itm_id]['dfls']['include_lst'] = False
            st.rerun()
    pass

def save_session_state_data():
    save_code = st.session_state['sb']['save_code']
    if len(save_code)>0:
        # check if empty
        if len(st.session_state['pf']['itms'].keys())==0:
            st.toast(f"No data to save", icon="❌")
            return

        # save itms, pf keys
        sd = {}
        sd['itms'] = st.session_state['itms']
        sd['pf'] = st.session_state['pf']

        # save
        sd_dir = f"{os.getcwd()}/saved_data"
        if not os.path.isdir(sd_dir):
            os.mkdir(sd_dir)

        save_fn = f"{save_code}.pkl"
        save_path = f"{os.getcwd()}/saved_data/{save_fn}"
        save2pkl(sd, save_path)
        st.toast(f"Data saved", icon="✔️")
    pass

def load_saved_data():
    save_code = st.session_state.sb['save_code']
    if len(save_code)>0:
        _cwd = os.getcwd()
        # check for saved_data dir
        sd_dir = f"{_cwd}/saved_data"
        if not os.path.isdir(sd_dir):
            os.mkdir(sd_dir)

        # check if save file is available
        save_code_fn = f"{save_code}.pkl"
        save_code_fpath = f"{_cwd}/saved_data/{save_code_fn}"
        if os.path.isfile(save_code_fpath):
            sd = load_pkl(save_code_fpath)
            for k in sd.keys():
                st.session_state[k] = sd[k]
            st.toast(f"Data loaded", icon="✔️")
        else:
            st.toast(f"{save_code} - not available", icon="❌")


def set_sidebar_elements():
    vers_num = '2026-01-28 1412'
    st.sidebar.image('./logo/compd_logo_white.png',)
    if st.sidebar.button('Clear Data'):
        reset_session_state_params_data()
    #st.sidebar.button('Deselect All Listings', on_click=deselect_lstings(), key='deselect_btn')
    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.sidebar.write(f'__Version__: {vers_num}')
    st.sidebar.write('__Source__: Ebay - AU')
    st.sidebar.write('__Portfolio__:')
    pf_names = ['Me','You']
    st.session_state['sb']['pf_names'] = pf_names
    st.session_state['sb']['pf_name'] = st.sidebar.selectbox('', pf_names, accept_new_options=False,
                                                             label_visibility='collapsed')
    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.session_state['sb']['item_loc'] = st.sidebar.radio("Item Location",
                                                        ['Australia only', 'Worldwide'], index=0)
    st.session_state['sb']['history_len'] = st.sidebar.radio("History",
                                                          ['1 week', '2 weeks','3 weeks','4 weeks',
                                                           '3 months','6 months'], index=1)

    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.session_state['sb']['show_sltd_lsts'] = st.sidebar.toggle("Selected Listings Only", value=False)
    #st.session_state['sb']['deselect_lsts'] = st.sidebar.toggle("Deselect Listings", value=False)
    st.session_state['sb']['show_pchart'] = st.sidebar.toggle("Show Price Chart", value=True)
    st.session_state['sb']['rm_best_offer'] = st.sidebar.toggle("Remove Best Offers", value=True)
    st.session_state['sb']['rm_graded'] = st.sidebar.toggle("Remove Graded Cards", value=True)
    st.session_state['sb']['mtch_card_num'] = st.sidebar.toggle("Match Card Num", value=True)

    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.sidebar.write('__Save Code__:')
    st.session_state['sb']['save_code'] = st.sidebar.text_input('', label_visibility='collapsed', placeholder='Enter save code')
    if st.sidebar.button('Save Data'):
        save_session_state_data()
    if st.sidebar.button('Load Data'):
        load_saved_data()

    # calc some params
    st.session_state['sb']['history_len_days'] = hist2days[st.session_state['sb']['history_len']]
    st.session_state['sb']['today'] = pd.Timestamp.today().normalize()
    st.session_state['sb']['hist_sdate'] = st.session_state['sb']['today'] - pd.Timedelta(days=st.session_state['sb']['history_len_days'])
    st.session_state['sb']['ipg'] = 60 if st.session_state['sb']['item_loc']=='Australia only' else 120

def set_tabs():
    tsearch, tport, ttrade = st.tabs(["Search", "Portfolio", "Trade"])
    st.session_state['tabs']['search'] = tsearch
    st.session_state['tabs']['portfolio'] = tport
    st.session_state['tabs']['trade'] = ttrade

@st.dialog(" ")
def show_more_listing_imgs(sold_url):
    driver = st.session_state.chrome_driver
    img_urls = get_lst_imgs(sold_url, driver)
    num_imgs = len(img_urls)
    img_size = 400

    if num_imgs>0:
        for ix, img_url in enumerate(img_urls):
            c1,c2,c3 = st.columns([0.01,0.98,0.01],)
            c2.image(f"{img_url}/s-l{img_size}.webp", caption=f"{ix+1}/{num_imgs}", width='content')
    else:
        st.write("No more images")

@st.dialog(" ")
def show_pf_itm_listing(itm_id):
    dfls = st.session_state.pf['itms'][itm_id]['dfls']
    st.dataframe(dfls,
                 column_order=['sold_date','title','price','auction_type','from_ctry_str'],
                 column_config={'sold_date':'Sold Date',
                                'title': 'Listing',
                                'price': st.column_config.NumberColumn('Price', format="$ %.1f"),
                                'auction_type': 'Auction Type',
                                'from_ctry_str': 'From Country',
                                },
                 hide_index=True)

def set_tsearch():
    def _set_stats_board():
        contr_stats = st.container(border=True)
        st.session_state.contr_stats = contr_stats
        contr_stats.write('#### Selected listings')

    def _set_pchart_container():
        contr_pchart = st.container(border=True)
        st.session_state.contr_pchart = contr_pchart

    def _update_stats_board():
        # df: selected listings, match history param
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst']]
        _dfls = _dfls.loc[_dfls['sold_date'] >= st.session_state['sb']['hist_sdate']]
        num_lsts = len(_dfls)
        if num_lsts > 0:
            stats = {'date_range_str': f"Date range: **{_dfls['sold_date'].min():%d %b %Y} - {_dfls['sold_date'].max():%d %b %Y}**",
                     'listings_str': f"Listings: **{num_lsts}**",
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
            if contr_stats.button('Add to Portfolio'):#, key=f"{itm_id}_{ix}_statb"):
                if itm_id not in st.session_state.pf['itms'].keys():
                    st.session_state.pf['itms'][itm_id] = {}
                st.session_state.pf['itms'][itm_id]['dfls'] = _dfls
                st.session_state.pf['itms'][itm_id]['stats'] = stats
                st.toast(f"Saved to Portfolio", icon="✔️")

    def _update_price_chart():
        # df: selected listings, match history param
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst']]
        _dfls = _dfls.loc[_dfls['sold_date'] >= st.session_state['sb']['hist_sdate']]

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

    ####################################################################################################################

    with st.session_state['tabs']['search']:
        # search bar
        sch_phrase = st.text_input(label='',
                                   label_visibility='collapsed',
                                   placeholder='Enter card name and number',
                                   key="sch_phrase_in")
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
        if itm_id not in st.session_state['itms'].keys():
            st.session_state['itms'][itm_id] = {}

            ipg = st.session_state['sb']['ipg']
            driver = st.session_state.chrome_driver
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)
            dfls['include_lst'] = False
            st.session_state['itms'][itm_id]['dfls'] = dfls
            st.session_state['itms'][itm_id]['sch_phrase'] = sch_phrase
            st.session_state['itms'][itm_id]['item_loc'] = item_loc
        else:
            dfls = st.session_state['itms'][itm_id]['dfls']

        # if no data returned
        if len(dfls)==0:
            st.write(f'### No listings returned for: {sch_phrase} - {loc_map[item_loc]}')
            return

        # prep the data to be displayed
        dfls = dfls.loc[dfls['sold_date'] >= st.session_state['sb']['hist_sdate']] # trim to match history param
        if st.session_state['sb']['rm_best_offer']: # remove best offers
            dfls = dfls.loc[dfls['auction_type']!='Best Offer']
        if st.session_state['sb']['show_sltd_lsts']: # show selected listings only
            dfls = dfls.loc[dfls['include_lst']]
            if len(dfls)==0:
                return

        # set some data containers
        if st.session_state['sb']['show_pchart']: # price chart
            _set_pchart_container()
        _set_stats_board() # add container to show price stats

        # display parameters
        c1_colw = [0.05,0.5, 0.45]
        c2_img_size = 300

        # display data
        #dfls = dfls.head(5)
        for ix, lst in dfls.iterrows():
            # container
            contr = st.container(border=True, horizontal=True)
            c1, c2, c3 = contr.columns(c1_colw,
                                       gap='small',
                                       vertical_alignment='center', ) # select, image, details

            # select button
            c1_key = f"{itm_id}_{ix}_c1"
            _button_state = c1.checkbox(label='',
                                        label_visibility='collapsed',
                                        key=c1_key,
                                        value=lst['include_lst'])
            st.session_state['itms'][itm_id]['dfls'].loc[ix, 'include_lst'] = _button_state

            # show img0
            c2_key = f"{itm_id}_{ix}_c2"
            c2.image(f"{lst['img_url0']}/s-l{c2_img_size}.webp", width='content')
            if c2.button('show more images', key=c2_key, width='content'):
                show_more_listing_imgs(lst['sold_url'])

            # details
            p = lst['price']
            p_str = f"{lst['price_str']}".replace('$',' ') if pd.isnull(p) else f"AU ${lst['price']}"
            write_style_str(parent_obj=c3, str_out=f"Sold  {lst['sold_date']:%d %b %Y}", color="#7D615E", font_size="1em")
            write_style_str(parent_obj=c3, str_out=lst['title'], color="#000000", font_size="1em", hyperlink=lst['sold_url'])
            strike_thr = True if lst['auction_type']=='Best Offer' else False
            write_style_str(parent_obj=c3, str_out=p_str, color="#7D615E", font_size="1.5em", font_w='bold', strike_through=strike_thr)
            write_style_str(parent_obj=c3, str_out=lst['auction_type'])
            write_style_str(parent_obj=c3, str_out=f"{lst['from_ctry_str']}", color="#7D615E", font_size="1em")

            # delete some keys
            delattr(st.session_state, c1_key)
            delattr(st.session_state, c2_key)

        # update containers above
        if st.session_state['sb']['show_pchart']:
            _update_price_chart()
        _update_stats_board()

def set_tport():
    def _set_portfolio_board():
        contr_pf = st.container(border=True)
        st.session_state.contr_pf = contr_pf
        contr_pf.write('#### Portfolio')

    def _update_portfolio_board():
        dfpf = st.session_state.pf['dfpf']
        if dfpf['include_itm'].sum()>0:
            contr_pf = st.session_state.contr_pf
            total = (dfpf[agg_by]*dfpf['include_itm']).sum()
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

    # include_itm, , num items, pcts - 90,80,75
    # display portfolio - use most recent lst as photo
    agg_by = 'mean'
    pcts_c1 = [0.9, 0.80, 0.70]
    pcts_c2 = [0.85, 0.75, 0.6]

    # so no error at the beginning
    itm_ids = st.session_state.pf['itms'].keys()
    # st.write(itm_ids)
    # st.write(st.session_state.pf)
    if len(itm_ids)==0:
        return

    # dfpf - itm_id, mean, median,
    dfpf = [pd.Series(st.session_state.pf['itms'][itm_id]['stats']).to_frame(itm_id) for itm_id in itm_ids]
    dfpf = pd.concat(dfpf, axis=1).T
    dfpf['include_itm'] = False
    st.session_state.pf['dfpf'] = dfpf
    #st.write(dfpf)

    # # pf stat calc
    # st.session_state.pf['total'] = dfpf[agg_by].sum()
    # for pct in pcts:
    #     st.session_state.pf[f"{int(pct * 100)}%"] = st.session_state.pf['total'] * pct

    tb_p = st.session_state['tabs']['portfolio']
    with tb_p:
        _set_portfolio_board()

        # display itms in pf
        for itm_id, row in dfpf.iterrows():
            stats = st.session_state.pf['itms'][itm_id]['stats']
            dfls = st.session_state.pf['itms'][itm_id]['dfls']

            contr = st.container(border=True)
            c1, c2, c3 = contr.columns([0.1,0.45,0.45], gap=None, vertical_alignment='center') # select, image, details

            _button_state = c1.checkbox(label='', label_visibility='collapsed', key=f"pf_{itm_id}_c1", value=True)
            #c1.write(_button_state)
            st.session_state.pf['dfpf'].loc[itm_id, 'include_itm'] = _button_state
            delattr(st.session_state, f"pf_{itm_id}_c1")


            # use first image from dfls
            img_size = '200'
            c2.image(f"{dfls['img_url0'].iloc[0]}/s-l{img_size}.webp")

            # compd itm info
            if c3.button('Show Listings', key=f"pf_{itm_id}_c3"):
                show_pf_itm_listing(itm_id)
            delattr(st.session_state, f"pf_{itm_id}_c3")

            sch_phrase = st.session_state['itms'][itm_id]['sch_phrase']
            item_loc = st.session_state['itms'][itm_id]['item_loc']
            c3.write(f"{sch_phrase}")
            c3.write(f"${row[agg_by]:.2f}")
            c3.write(f"{item_loc}")

        #st.write(st.session_state.pf['dfpf'])
        _update_portfolio_board()
    pass


def compd_desktop():
    #st.write('compd - desktop')

    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    set_tport()

if __name__ == '__main__':
    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    set_tport()
