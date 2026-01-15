import streamlit as st
from src.get_screen_info import get_screen_data



def set_screen_data(mobile_res=False):
    if mobile_res:
        st.session_state.screen_data = {'device':'iphone_16',
                                        'screen_width':393,
                                        'screen_height':852}
    else:
        st.session_state.screen_data = get_screen_data()

def set_screen_contr():
    # sets the boundarys of the web app based on the screen data gathered
    st.write(st.session_state.screen_data)
    st.container(border=True,
                 # width=st.session_state.screen_data['screen_width'],
                 # height=st.session_state.screen_data['screen_height'],
                 width='stretch',
                 height='stretch',
                 horizontal_alignment='left', vertical_alignment='top',
                 key='screen_contr')

    st.container(border=True,
                 width=st.session_state.screen_data['screen_width'],
                 height=st.session_state.screen_data['screen_height'],
                 horizontal_alignment='left', vertical_alignment='top',
                 key='screen_contr2')

def set_sidebar_elements():
    pass









if __name__ == '__main__':
    # manually enter itms to comp - along with UI(dialogue) to enter hist sale prices
    # clear data butotn
    # bulk mode - common($0.2), reverse($1), custom1(text_box), custom2(text-box)
    # total
    # dynamic based on detected screen size

    set_screen_data(mobile_res=True)
    set_screen_contr()
    set_sidebar_elements()
