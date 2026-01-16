from streamlit_js_eval import streamlit_js_eval
import streamlit as st

def get_screen_data(key=''):
    dim_screen = {}
    dim_screen['screen_width'] = streamlit_js_eval(js_expressions='screen.width', key=f"w_{key}")
    dim_screen['screen_height'] = streamlit_js_eval(js_expressions='screen.height', key=f"h_{key}")

    dim_screen['win_iwidth'] = streamlit_js_eval(js_expressions='window.innerWidth', key=f"iw_{key}")
    dim_screen['win_iheight'] = streamlit_js_eval(js_expressions='window.innerHeight', key=f"ih_{key}")

    dim_screen['win_owidth'] = streamlit_js_eval(js_expressions='window.outerWidth', key=f"ow_{key}")
    dim_screen['win_oheight'] = streamlit_js_eval(js_expressions='window.outerHeight', key=f"oh_{key}")
    return dim_screen

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




if __name__ == '__main__':
    get_screen_data()
    pass
