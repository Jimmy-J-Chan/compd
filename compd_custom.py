import streamlit as st
from src.manage_screen_res import *
from conf.config import *

# page settings
st.set_page_config(page_title="Compd Custom",
                   #layout='wide',
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )


def reset_session_state_params_data():
    # only reset itms and pf, keep sb params and tabs
    pass

def set_sidebar_elements():
    st.sidebar.image('./logo/compd_logo_white.png', )
    if st.sidebar.button('Clear Data'):
        reset_session_state_params_data()
    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    pass









if __name__ == '__main__':
    # manually enter itms to comp - along with UI(dialogue) to enter hist sale prices
    # clear data butotn
    # bulk mode - common($0.2), reverse($1), custom1(text_box), custom2(text-box)
    # total
    # dynamic based on detected screen size

    # set screen requirements
    set_screen_data(mobile_res=True)
    set_screen_contr()

    # app contents
    with st.session_state.screen_contr:
        set_sidebar_elements()


