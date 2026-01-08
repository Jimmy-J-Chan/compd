import streamlit as st
import pandas as pd
from pandas.core.ops.missing import mask_zero_div_zero

from src.get_ebayau_listing_data import get_ebayau_listing_data, get_lst_imgs, get_chrome_driver, close_chrome_driver

# page settings
st.set_page_config(page_title="Compd",
                   layout='wide', #"centered",
                   initial_sidebar_state='expanded',
                   )

# params
weeks2days = {'1 week':7, '2 weeks':14,'3 weeks':21,'4 weeks':28,
              '3 months':30*3, '6 months':30*6, '12 months':30*12,}
loc_map = {'Australia only': 'AU',
           'Worldwide': 'WRLD'}
ss_g = ['sb', 'itms', 'pf','tabs']

def set_scroll2top_button():
    st.html("<div id='top'></div>")
    st.html("""
        <a href="#top" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #ff4b4b;
            color: white;
            text-decoration: none;
            padding: 10px 15px;
            border-radius: 50px;
            font-weight: bold;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
            z-index: 9999;
        ">
            ↑ Top
        </a>
    """)

def write_style_str(parent_obj=None, str_out=None, color=None, font_size=None, font_w=None, strike_through=False):
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
    if parent_obj is not None:
        parent_obj.markdown(html_str, unsafe_allow_html=True)
    else:
        st.markdown(html_str, unsafe_allow_html=True)
    pass

def set_chrome_driver():
    if 'chrome_driver' not in st.session_state.keys():
        st.session_state.chrome_driver = get_chrome_driver()

def set_session_state_groups():
    for g in ss_g:
        if g not in st.session_state.keys():
            st.session_state[g] = {}
            if g=='pf':
                st.session_state.pf['itms'] = {}

def reset_session_state_params():
    for g in ss_g:
        st.session_state[g] = {}

def set_sidebar_elements():
    st.sidebar.title("*:red[Compd]* :chart_with_upwards_trend: :chart_with_downwards_trend:",)
    st.sidebar.write('### Source: Ebay - AU')
    st.session_state['sb']['item_loc']=st.sidebar.radio("Item Location",
                                                        ['Australia only', 'Worldwide'])
    st.session_state['sb']['history_len'] = st.sidebar.radio("History",
                                                          ['1 week', '2 weeks','3 weeks','4 weeks',
                                                           '3 months','6months','12months'])
    st.session_state['sb']['history_len_days'] = weeks2days[st.session_state['sb']['history_len']]
    st.session_state['sb']['today'] = pd.Timestamp.today().normalize()
    st.session_state['sb']['hist_sdate'] = st.session_state['sb']['today'] - pd.Timedelta(days=st.session_state['sb']['history_len_days'])

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
    img_size = '400'
    num_imgs = len(img_urls)

    if num_imgs>0:
        for ix, img_url in enumerate(img_urls):
            c1,c2,c3 = st.columns([0.15,0.7,0.15])
            c2.image(f"{img_url}/s-l{img_size}.webp", caption=f"{ix+1}/{num_imgs}")
    else:
        st.write("No more images")



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
        _dfls = st.session_state['itms'][sch_phrase]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst']]
        num_lsts = len(_dfls)
        if num_lsts > 0:
            contr_stats = st.session_state.contr_stats
            contr_stats.write(f"Date range: **{_dfls['sold_date'].min():%d %b %Y} - {_dfls['sold_date'].max():%d %b %Y}**")
            contr_stats.write(f"Listings: **{num_lsts}**")
            contr_stats.write(f"Price range: **\${_dfls['price'].min()} - \${_dfls['price'].max()}**")
            contr_stats.write(f"Mean: **${_dfls['price'].mean():.2f}**")
            contr_stats.write(f"Median: **${_dfls['price'].median():.2f}**")
            if contr_stats.button('Add to Portfolio', key=f"{sch_phrase}_{ix}_statb"):
                if sch_phrase not in st.session_state.pf['itms'].keys():
                    st.session_state.pf['itms'][sch_phrase] = {}
                st.session_state.pf['itms'][sch_phrase]['dfls'] = _dfls


    tb_s = st.session_state['tabs']['search']
    driver = st.session_state.chrome_driver
    with tb_s:
        sch_phrase = st.text_input(label='',label_visibility='collapsed', placeholder='Enter card name and number')
        item_loc = st.session_state['sb']['item_loc']

        if len(sch_phrase) == 0:
            # show nothing
            return
        elif len(sch_phrase.split(' '))<2:
            st.write('### Invalid search: enter item name and number')
            return

        # use itm_id instead of sch_phrase - itm_id = {sch_phrase}_{AU/WRLD} #TODO
        itm_id = f"{sch_phrase}_{loc_map[item_loc]}"
        if sch_phrase not in st.session_state['itms'].keys():
            st.session_state['itms'][sch_phrase] = {}
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, driver)
            dfls['include_lst'] = False
            st.session_state['itms'][sch_phrase]['dfls'] = dfls
        else:
            dfls = st.session_state['itms'][sch_phrase]['dfls']
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
            c12, c2, c3 = contr.columns([0.1,0.45,0.45], gap=None, vertical_alignment='center') # select, image, details

            # button to select listing - use on_change, update using current state of button
            # update stats box, include_lst
            _button_state = c12.checkbox(label='', label_visibility='collapsed',
                                         key=f"{sch_phrase}_{ix}_c1")
            st.session_state['itms'][sch_phrase]['dfls'].loc[ix, 'include_lst'] = _button_state

            # show img0 - 140, 500, 960, 1600
            img_size = '300'
            c2.image(f"{lst['img_url0']}/s-l{img_size}.webp")
            if c3.button('show more images', key=f"{sch_phrase}_{ix}_c2"):
                show_more_listing_imgs(lst['sold_url'])

            # display sold info
            p = lst['price']
            p_str = f"{lst['price_str']}".replace('$',' ') if pd.isnull(p) else f"AU ${lst['price']}"
            write_style_str(parent_obj=c3, str_out=f"Sold  {lst['sold_date']:%d %b %Y}", color="#7D615E", font_size="1em")
            write_style_str(parent_obj=c3, str_out=lst['title'], color="#000000", font_size="1em")
            strike_thr = True if lst['auction_type']=='Best Offer' else False
            write_style_str(parent_obj=c3, str_out=p_str, color="#7D615E", font_size="1.5em", font_w='bold', strike_through=strike_thr)
            write_style_str(parent_obj=c3, str_out=lst['auction_type'])

        _update_stats_board()
        # st.write(st.session_state['itms'][sch_phrase]['dfls'])
        st.write(st.session_state.itms)
        st.write(st.session_state.pf)

def set_tport():
    def _set_portfolio_board():
        contr_pf = st.container(border=True)
        st.session_state.contr_pf = contr_pf
        contr_pf.write('#### Portfolio')

    # total, num items, pcts - 90,80,75
    # display portfolio - use most recent lst as photo


    tb_p = st.session_state['tabs']['portfolio']
    sch_phrases = st.session_state['itms'].keys()
    with tb_p:
        _set_portfolio_board()
        for ix, sch_phrase in enumerate(sch_phrases):
            dfls = st.session_state['itms'][sch_phrase]['dfls']


    pass


if __name__ == '__main__':
    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    #set_tport()

    pass