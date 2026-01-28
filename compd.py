import streamlit as st
from src.manage_screen_res import get_screen_width
from compd_desktop import compd_desktop
from compd_mobile import compd_mobile

ALWAYS_USE_DESKTOP = False



def run_compd_by_screen_width():
    screen_width = get_screen_width() # TODO: remove empty space
    if screen_width is not None:
        if (screen_width<1000) & (not ALWAYS_USE_DESKTOP):
            compd_mobile()
        else:
            compd_desktop()

def run_compd():
    compd_mobile()

if __name__ == '__main__':
    run_compd()
    pass