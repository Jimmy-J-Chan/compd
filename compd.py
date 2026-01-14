import streamlit as st
import pandas as pd
from src.get_ebayau_listing_data import get_ebayau_listing_data, get_lst_imgs, get_chrome_driver
from conf.config import *

# page settings
st.set_page_config(page_title="Compd",
                   #layout='wide',
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )


def set_scroll2top_button():
    st.html("<div id='top'></div>")
    st.markdown(
        """
        <a href="#top" style="
            position: fixed;
            top: 90%;
            right: 0px;
            transform: translateY(-50%);
            background-color: #ff4b4b;
            color: white;
            text-decoration: none;
            padding: 10px 15px;
            border-radius: 10px 0px 0px 10px; /* Rounded only on the left side */
            border-radius: 50px
            font-weight: bold;
            box-shadow: -2px 2px 10px rgba(0,0,0,0.2);
            z-index: 9999;
            text-combine-upright: all;
        ">
            ↑ Top
        </a>
        """,
        unsafe_allow_html=True
    )


def write_style_str(parent_obj=None, str_out=None, color=None, font_size=None, font_w=None, strike_through=False,
                    hyperlink=None):
    style_str = ''
    if color is not None:
        style_str = style_str + f"color:{color};"
    if font_size is not None:
        style_str = style_str + f"font-size:{font_size};"
    if font_w is not None:
        style_str = style_str + f"font-weight:{font_w};"
    if strike_through:
        style_str = style_str + f"text-decoration: line-through;"

    html_str = f"<span style='{style_str}'>{str_out}</span>"

    if hyperlink is not None:
        html_str = f'<a href="{hyperlink}" target="_blank" style="text-decoration: none;">{html_str}</a>'

    if parent_obj is not None:
        parent_obj.markdown(html_str, unsafe_allow_html=True)
    else:
        st.markdown(html_str, unsafe_allow_html=True)
    pass

def set_chrome_driver():
    if 'chrome_driver' not in st.session_state.keys():
        st.session_state.chrome_driver = get_chrome_driver()

def set_session_state_groups(reset_params=False):
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

def set_sidebar_elements():
    #st.sidebar.title("*:red[Compd]* :chart_with_upwards_trend: :chart_with_downwards_trend:",)
    st.sidebar.image('./logo/compd_logo_white.png',)
    if st.sidebar.button('Clear Data'):
        reset_session_state_params_data()
    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.sidebar.write('__Source__: Ebay - AU')
    st.session_state['sb']['item_loc']=st.sidebar.radio("Item Location",
                                                        ['Australia only', 'Worldwide'], index=0)
    st.session_state['sb']['history_len'] = st.sidebar.radio("History",
                                                          ['1 week', '2 weeks','3 weeks','4 weeks',
                                                           '3 months','6months','12months'], index=3)
    st.session_state['sb']['history_len_days'] = weeks2days[st.session_state['sb']['history_len']]
    st.session_state['sb']['today'] = pd.Timestamp.today().normalize()
    st.session_state['sb']['hist_sdate'] = st.session_state['sb']['today'] - pd.Timedelta(days=st.session_state['sb']['history_len_days'])
    st.session_state['sb']['ipg'] = 60 if st.session_state['sb']['item_loc']=='Australia only' else 120

    # st.write(st.session_state['sb']['today'])
    # st.write(st.session_state['sb']['hist_sdate'])
    #st.sidebar.button('Reset', on_click=reset_session_state_params())
    # st.session_state['sb']['show_only']=st.sidebar.radio("Show Only",
    #                                                      ['Sold/Completed Items', 'Current Listings'])
    # st.session_state['sb']['buy_fmt']=st.sidebar.radio("Buying Format",
    #                                                    ['All','Auction', 'Buy It Now'])

def set_tabs():
    tsearch, tport, ttrade = st.tabs(["Search", "Portfolio", "Trade"])
    st.session_state['tabs']['search'] = tsearch
    st.session_state['tabs']['portfolio'] = tport
    st.session_state['tabs']['trade'] = ttrade

@st.dialog(" ")
def show_more_listing_imgs(sold_url):
    driver = st.session_state.chrome_driver
    img_urls = get_lst_imgs(sold_url, driver)
    img_size = img_size_ts # '400' # fit to screen width
    num_imgs = len(img_urls)

    if num_imgs>0:
        for ix, img_url in enumerate(img_urls):
            c1,c2,c3 = st.columns([0.15,0.7,0.15])
            c2.image(f"{img_url}/s-l{img_size}.webp", caption=f"{ix+1}/{num_imgs}")
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
        # contr_stats.write(f"Date range: N/A - N/A")
        # contr_stats.write(f"Price range: N/A - N/A")
        # contr_stats.write(f"Mean: N/A")
        # contr_stats.write(f"Median: N/A")

    def _update_stats_board():
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst']]
        num_lsts = len(_dfls)
        if num_lsts > 0:
            stats = {'date_range_str': f"Date range: **{_dfls['sold_date'].min():%d %b %Y} - {_dfls['sold_date'].max():%d %b %Y}**",
                     'listings_str': f"Listings: **{num_lsts}**",
                     'price_range_str': f"Price range: **\${_dfls['price'].min()} - \${_dfls['price'].max()}**",
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

    tb_s = st.session_state['tabs']['search']
    driver = st.session_state.chrome_driver
    with tb_s:
        sch_phrase = st.text_input(label='', label_visibility='collapsed',
                                   placeholder='Enter card name and number', key="sch_phrase_in")
        item_loc = st.session_state['sb']['item_loc']
        ipg = st.session_state['sb']['ipg']
        if len(sch_phrase) == 0:
            # show nothing
            return
        elif len(sch_phrase.split(' '))<2:
            st.write('### Invalid search: enter item name and number')
            return

        # use itm_id instead of sch_phrase - itm_id = {sch_phrase}_{AU/WRLD} #TODO
        itm_id = f"{sch_phrase}_{loc_map[item_loc]}"
        if itm_id not in st.session_state['itms'].keys():
            st.session_state['itms'][itm_id] = {}
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)
            dfls['include_lst'] = False
            st.session_state['itms'][itm_id]['dfls'] = dfls
            st.session_state['itms'][itm_id]['sch_phrase'] = sch_phrase
            st.session_state['itms'][itm_id]['item_loc'] = item_loc
        else:
            dfls = st.session_state['itms'][itm_id]['dfls']

        if len(dfls)==0:
            st.write(f'### No listings returned for: {sch_phrase} - {loc_map[item_loc]}')
            return

        dfls = dfls.loc[dfls['sold_date'] >= st.session_state['sb']['hist_sdate']]

        # add container to show price stats
        # date range, mean, median, price range: min, max
        _set_stats_board()

        # load listing data onto search tab
        tmpdf = dfls #.head(3)
        #st.write(tmpdf)
        for ix, lst in tmpdf.iterrows():
            # setup container for each listing
            contr = st.container(border=True)
            #c11,c12,c13, c2, c3 = contr.columns([0.025,0.05,0.025,0.45,0.45], gap=None, vertical_alignment='center') # select, image, details
            c1, c2, c3 = contr.columns([0.1,0.45,0.45], gap=None, vertical_alignment='center') # select, image, details

            # button to select listing - use on_change, update using current state of button
            # update stats box, include_lst
            _button_state = c1.checkbox(label='', label_visibility='collapsed', key=f"{itm_id}_{ix}_c1")
            st.session_state['itms'][itm_id]['dfls'].loc[ix, 'include_lst'] = _button_state
            delattr(st.session_state, f"{itm_id}_{ix}_c1")

            # show img0 - 140, 500, 960, 1600
            img_size = img_size_ts # '300'
            c2.image(f"{lst['img_url0']}/s-l{img_size}.webp")
            if c3.button('show more images', key=f"{itm_id}_{ix}_c2"):
                show_more_listing_imgs(lst['sold_url'])
            delattr(st.session_state, f"{itm_id}_{ix}_c2")

            # display sold info
            p = lst['price']
            p_str = f"{lst['price_str']}".replace('$',' ') if pd.isnull(p) else f"AU ${lst['price']}"
            write_style_str(parent_obj=c3, str_out=f"Sold  {lst['sold_date']:%d %b %Y}", color="#7D615E", font_size="1em")
            write_style_str(parent_obj=c3, str_out=lst['title'], color="#000000", font_size="1em", hyperlink=lst['sold_url'])
            strike_thr = True if lst['auction_type']=='Best Offer' else False
            write_style_str(parent_obj=c3, str_out=p_str, color="#7D615E", font_size="1.5em", font_w='bold', strike_through=strike_thr)
            write_style_str(parent_obj=c3, str_out=lst['auction_type'])
            write_style_str(parent_obj=c3, str_out=f"{lst['from_ctry_str']}", color="#7D615E", font_size="1em")

        _update_stats_board()
        # st.write(st.session_state)
        # st.write(st.session_state['itms'][sch_phrase]['dfls'])
        # st.write(st.session_state.itms)
        # st.write(st.session_state.pf)

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
            for pct in pcts:
                _str = f"{int(pct*100)}%"
                contr_pf.write(f"{_str}: **${total*pct:.2f}**")
        pass

    # include_itm, , num items, pcts - 90,80,75
    # display portfolio - use most recent lst as photo
    agg_by = 'mean'
    pcts = [0.9, 0.80, 0.75, 0.7]

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


if __name__ == '__main__':
    # from src.get_screen_info import get_client_screen_data
    # dim_screen = get_client_screen_data('1')
    # st.write(dim_screen)

    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    set_tport()

    #st.write(st.session_state)
    pass