import streamlit as st
from src.manage_screen_res import get_screen_data
from compd_desktop import compd_desktop
from compd_mobile import compd_mobile



if __name__ == '__main__':
    sd = get_screen_data()
    st.write(sd)

    # if sd['screen_width']<1000:
    #     compd_mobile()
    # else:
    #     compd_desktop()
    pass