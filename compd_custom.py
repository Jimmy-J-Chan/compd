import streamlit as st
from src.get_screen_info import get_screen_data
from conf.config import *

# page settings
st.set_page_config(page_title="Compd Custom",
                   #layout='wide',
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )

def set_screen_data(mobile_res=False):
    if mobile_res:
        # https://www.ios-resolution.com/
        st.session_state.screen_data = {'device':'iphone_16',
                                        'screen_width':393,
                                        'screen_height':852}
    else:
        st.session_state.screen_data = get_screen_data()

def set_screen_contr():
    # sets the width boundary of the web app based on the screen data gathered
    screen_contr = st.container(border=True,
                                 width=st.session_state.screen_data['screen_width'],
                                 height='content', # match height of contents
                                 horizontal_alignment='left', vertical_alignment='top',)
    st.session_state.screen_contr = screen_contr

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


