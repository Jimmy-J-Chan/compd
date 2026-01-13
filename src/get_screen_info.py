import streamlit as st
from streamlit_js_eval import streamlit_js_eval


def get_client_screen_data(key=''):
    dim_screen = {}
    dim_screen['screen_width'] = streamlit_js_eval(js_expressions='screen.width', key=f"w_{key}")
    dim_screen['screen_height'] = streamlit_js_eval(js_expressions='screen.height', key=f"h_{key}")

    dim_screen['win_iwidth'] = streamlit_js_eval(js_expressions='window.innerWidth', key=f"iw_{key}")
    dim_screen['win_iheight'] = streamlit_js_eval(js_expressions='window.innerHeight', key=f"ih_{key}")

    dim_screen['win_owidth'] = streamlit_js_eval(js_expressions='window.outerWidth', key=f"iw_{key}")
    dim_screen['win_oheight'] = streamlit_js_eval(js_expressions='window.outerHeight', key=f"ih_{key}")
    return dim_screen

if __name__ == '__main__':
    get_client_screen_data()
    pass
