import pickle
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import urllib.parse


def set_scroll2top_button():
    st.html("<div id='top'></div>")
    st.markdown(
        """
        <a href="#top" style="
            position: fixed;
            top: 88%;
            right: 0px;
            transform: translateY(-50%);
            background-color: #ff4b4b;
            color: white;
            text-decoration: none;
            padding: 10px 15px;
            border-radius: 10px 0px 0px 10px; /* Rounded only on the left side */
            font-weight: bold;
            box-shadow: -2px 2px 10px rgba(0,0,0,0.2);
            z-index: 9999;
            text-combine-upright: all;
        ">
            ↑ Top
        </a>
        """,
        unsafe_allow_html=True
    )

def get_chrome_driver(headless=True, use_local=False, max_window=False):
    # Set up Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Uncomment to run without a visible window
    #chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    #iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
    #chrome_options.add_argument(f"user-agent={iphone_ua}")
    #chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("window-size=1280,800")
    #chrome_options.add_argument("window-size=393,852")
    chrome_options.add_argument("--disable-gpu")

    if (st.context.url in ['http://localhost:8501']) | use_local:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
                                  options=chrome_options)
    if max_window:
        driver.maximize_window()
    return driver

def set_chrome_driver():
    if 'chrome_driver' not in st.session_state.keys():
        st.session_state.chrome_driver = get_chrome_driver(max_window=True)

def write_style_str(parent_obj=None, str_out=None, color=None, font_size=None, font_w=None, strike_through=False,
                    hyperlink=None):
    style_str = ''
    if color is not None:
        style_str = style_str + f"color:{color};"
    if font_size is not None:
        style_str = style_str + f"font-size:{font_size};"
    if font_w is not None:
        style_str = style_str + f"font-weight:{font_w};"
    if strike_through:
        style_str = style_str + f"text-decoration: line-through;"

    html_str = f"<span style='{style_str}'>{str_out}</span>"

    if hyperlink is not None:
        html_str = f'<a href="{hyperlink}" target="_blank" style="text-decoration: none;">{html_str}</a>'

    if parent_obj is not None:
        parent_obj.markdown(html_str, unsafe_allow_html=True)
    else:
        st.markdown(html_str, unsafe_allow_html=True)
    pass

def reduce_md_spacing(gap='0px'):
    st.markdown(f"""
        <style>
        /* Reduce gap between ALL markdown blocks */
        [data-testid="stMarkdownContainer"] p {{
            margin-bottom: {gap} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    pass

def insert_spacer():
    st.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    pass

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def save2pkl(obj, save_path):
    with open(save_path, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_pkl(save_path):
    with open(save_path, 'rb') as file:
        obj = pickle.load(file)
    return obj

def encode_str(str_phrase, param_name=''):
    enc_str = urllib.parse.urlencode({param_name: str_phrase,})
    if param_name=='':
        enc_str = enc_str[1:].strip()
    return enc_str




if __name__ == '__main__':
    enc_str = encode_str("charizard 4/102", )
    pass