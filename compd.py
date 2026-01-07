import streamlit as st
import pandas as pd
from pandas.core.ops.missing import mask_zero_div_zero

from src.get_ebayau_listing_data import get_ebayau_listing_data, get_lst_imgs, get_chrome_driver, close_chrome_driver

# page settings
st.set_page_config(page_title="Compd",
                   layout="centered",
                   initial_sidebar_state='expanded',
                   )

# params
weeks2days = {'1 week':7, '2 weeks':14,'3 weeks':21,'4 weeks':28}
ss_g = ['sb', 'itms', 'pf','tabs']

def set_chrome_driver():
    if 'chrome_driver' not in st.session_state.keys():
        st.session_state.chrome_driver = get_chrome_driver()

def set_session_state_groups():
    for g in ss_g:
        if g not in st.session_state.keys():
            st.session_state[g] = {}

def reset_session_state_params():
    for g in ss_g:
        st.session_state[g] = {}

def set_sidebar_elements():
    st.sidebar.title("*:red[Compd]* :chart_with_upwards_trend: :chart_with_downwards_trend:",)
    st.sidebar.write('### Source: Ebay - AU')
    st.session_state['sb']['item_loc']=st.sidebar.radio("Item Location",
                                                        ['Australia only', 'Worldwide'])
    st.session_state['sb']['history_len'] = st.sidebar.radio("History",
                                                          ['1 week', '2 weeks','3 weeks','4 weeks'])
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
    tsearch, tport = st.tabs(["Search", "Portfolio"])
    st.session_state['tabs']['search'] = tsearch
    st.session_state['tabs']['portfolio'] = tport

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


def set_tsearch_elements():
    tb_s = st.session_state['tabs']['search']
    driver = st.session_state.chrome_driver

    with tb_s:
        sch_phrase = st.text_input(label='',label_visibility='collapsed', placeholder='Enter card name and number')
        dfls = get_ebayau_listing_data(sch_phrase, driver)

        if len(dfls)==0:
            # show nothing
            return

        # some parsing
        dfls['include_lst'] = False
        dfls = dfls.loc[dfls['sold_date']>=st.session_state['sb']['hist_sdate']]

        # save data to ss/itms
        st.session_state['itms'][sch_phrase] = {}
        st.session_state['itms'][sch_phrase]['dfls'] = dfls

        # load listing data onto search tab
        tmpdf = dfls.head(3)
        tmpdf.loc[63,'price'] = None
        st.write(tmpdf)
        for ix, lst in tmpdf.iterrows():
            # setup container for each listing
            contr = st.container(border=True)
            #c11,c12,c13, c2, c3 = contr.columns([0.025,0.05,0.025,0.45,0.45], gap=None, vertical_alignment='center') # select, image, details
            c12, c2, c3 = contr.columns([0.1,0.45,0.45], gap=None, vertical_alignment='center') # select, image, details

            # button to select listing
            if c12.checkbox(label='', label_visibility='collapsed', key=f"{sch_phrase}_{ix}_c1",):
                st.session_state['itms'][sch_phrase]['dfls'].loc[ix, 'include_lst'] = True

            # show img0 - 140, 500, 960, 1600
            img_size = '300'
            c2.image(f"{lst['img_url0']}/s-l{img_size}.webp")
            if c2.button('show more images', key=f"{sch_phrase}_{ix}_c2"):
                show_more_listing_imgs(lst['sold_url'])

            # display sold info
            p = lst['price']
            c3.markdown(f"""
                        <span style='color:#7D615E; font-size:1em;'>Sold  {lst['sold_date']:%d %b %Y}</span>            
                        """, unsafe_allow_html=True)

            c3.markdown(f"""
                        <span style='color:#000000; font-size:1em;'>{lst['title']}</span>            
                        """, unsafe_allow_html=True)

            p_str = f"{lst['price_str']}" if pd.isnull(p) else f"AU ${lst['price']}"
            c3.markdown(f"""
                        <span style='color:#7D615E; font-size:1.5em; font-weight: bold;'>{p_str}</span>            
                        """, unsafe_allow_html=True)

            c3.markdown(f"{lst['auction_type']}")


        #st.write(st.session_state['itms'][sch_phrase]['dfls'].head())



if __name__ == '__main__':
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch_elements()



    #############
    #st.write(st.session_state)
    pass