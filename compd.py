import streamlit as st

# page settings
st.set_page_config(page_title="Compd",
                   layout="centered",
                   initial_sidebar_state='expanded',
                   )

# params
ss_g = ['sb', 'itms', 'pf','tabs']


def set_session_state_groups():
    for g in ss_g:
        if g not in st.session_state.keys():
            st.session_state[g] = {}

def reset_session_state_params():
    for g in ss_g:
        st.session_state[g] = {}

def set_sidebar_elements():
    st.sidebar.title("*:red[Compd]* :chart_with_upwards_trend: :chart_with_downwards_trend:",)
    #st.sidebar.button('Reset', on_click=reset_session_state_params())
    st.session_state['sb']['item_loc']=st.sidebar.radio("Item Location",
                                                        ['Australia only', 'Worldwide'])
    st.session_state['sb']['show_only']=st.sidebar.radio("Show Only",
                                                         ['Sold/Completed Items', 'Current Listings'])
    st.session_state['sb']['buy_fmt']=st.sidebar.radio("Buying Format",
                                                       ['All','Auction', 'Buy It Now'])

def set_tabs():
    tsearch, tport = st.tabs(["Search", "Portfolio"])
    st.session_state['tabs']['search'] = tsearch
    st.session_state['tabs']['portfolio'] = tport

def set_tsearch_elements():
    tb_s = st.session_state['tabs']['search']


    with tb_s:
        c1, c2 = st.columns([0.5,0.5])
        sch_phrase = c1.text_input(label='',label_visibility='collapsed', placeholder='Enter card name and number')
        dfls = get_ebayau_listing_data(sch_phrase)

        # save data to ss/itms
        st.session_state['itms'][sch_phrase] = {}
        st.session_state['itms'][sch_phrase]['dfls'] = dfls



if __name__ == '__main__':
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch_elements()

    # st.divider()
    #st.write(st.session_state.itms)
    pass