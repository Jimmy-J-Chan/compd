import streamlit as st
from src.manage_screen_res import get_screen_width
from compd_desktop import compd_desktop
from compd_mobile import compd_mobile

ALWAYS_USE_DESKTOP = True


if __name__ == '__main__':
    screen_width = get_screen_width()
    if screen_width is not None:
        if (screen_width<1000) & (not ALWAYS_USE_DESKTOP):
            compd_mobile()
        else:
            compd_desktop()