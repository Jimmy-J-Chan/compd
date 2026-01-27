import pandas as pd
import streamlit as st
from conf.config import *
from src.common import set_scroll2top_button

# page settings
st.set_page_config(page_title="Compd Custom",
                   #layout='wide',
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )


# def reset_data():
#     if 'df' in st.session_state['bulk'].keys():
#         _df = st.session_state['bulk']['df']
#         _df = _df.loc[_df['Name'].isin(['Common', 'Reverse Holo'])]
#         _df['Quantity'] = 0.
#         st.session_state['bulk']['df'] = _df
#     #st.rerun()
#     pass

def set_session_state_groups():
    for g in ['tabs','bulk','me','you','trade']:
        if g not in st.session_state.keys():
            st.session_state[g] = {}

def set_sidebar_elements():
    vers_num = '2026-01-27 1602'
    st.sidebar.image('./logo/compd_logo_white.png',)
    # if st.sidebar.button('Clear Data'):
    #     reset_data()
    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.sidebar.write(f'__Version__: {vers_num}')
    st.sidebar.markdown('<hr style="margin: 0px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    st.session_state['trade_pct'] = st.sidebar.number_input("Trade percentage (%)", min_value=0, max_value=100,
                                                            value=80, step=5)


def set_tabs():
    tbulk, tme, tyou, ttrade = st.tabs(["Bulk", "Me", "You", "Trade"])
    st.session_state['tabs']['bulk'] = tbulk
    st.session_state['tabs']['me'] = tme
    st.session_state['tabs']['you'] = tyou
    st.session_state['tabs']['trade'] = ttrade

def set_total_header(tab_name):
    contr_header = st.container(border=True)
    st.session_state[tab_name]['contr_header'] = contr_header
    _bstr = '#### Bulk Calculator' if tab_name == 'bulk' else f"### Portfolio - {tab_name.capitalize()}"
    contr_header.write(_bstr)

def update_total_header(tab_name):
    contr_header = st.session_state[tab_name]['contr_header']
    df = st.session_state[tab_name]['df']

    df = df.loc[df['Quantity']>0]
    num_itms = df['Quantity'].sum()
    if num_itms>0:
        total = (df['Quantity']*df['Price']).sum()
        contr_header.write(f"Items: **{num_itms:.0f}**")
        contr_header.write(f"Total: **${total:.2f}**")

        # print total(pct) if pf=you
        # trade at the give pct
        if tab_name == 'you':
            pct_trade = st.session_state['trade_pct']
            contr_header.write(f"Total ({pct_trade}%): **${total*pct_trade/100:.2f}**")
    pass


def set_tbulk():
    tab_name = 'bulk'
    df = pd.DataFrame(columns=['Name', 'Quantity', 'Price'])
    df = df.astype({'Name':str,
                    'Quantity':float,
                    'Price':float})
    df['Name'] = ['Common','Reverse Holo']
    df['Quantity'] = 0.
    df['Price'] = [0.2,1]

    with st.session_state['tabs']['bulk']:
        set_total_header(tab_name)

        # display inputs
        df2 = st.data_editor(df, num_rows='dynamic', hide_index=True, placeholder=None,
                       column_config={'Price': st.column_config.NumberColumn('Price', format="$ %.2f"),
                                      'Quantity': st.column_config.NumberColumn('Quantity', format="%.0f")
                                      }
                       )

        st.session_state[tab_name]['df'] = df2
        update_total_header(tab_name)
        pass

    # st.write(st.session_state[tab_name]['df'])
    # st.write(st.session_state[tab_name]['df'].dtypes)

def set_tcustom(tab_name):
    df = pd.DataFrame(columns=['Name', 'Quantity', 'Price'])
    df = df.astype({'Name': str,
                    'Quantity': float,
                    'Price': float})
    with st.session_state['tabs'][tab_name]:
        set_total_header(tab_name)

        # display inputs
        df2 = st.data_editor(df, num_rows='dynamic', hide_index=True, placeholder=None, key=f'df2_{tab_name}',
                             column_order=['Name', 'Price'],#['Name', 'Quantity', 'Price'],
                       column_config={'Price': st.column_config.NumberColumn('Price', format="$ %.2f"),
                                      'Quantity': st.column_config.NumberColumn('Quantity', format="%.0f")
                                      }
                       )

        mask = df2['Quantity'].isnull()
        df2.loc[mask,'Quantity'] = 0.
        st.session_state[tab_name]['df'] = df2
        update_total_header(tab_name)
        pass

def set_ttrade():
    # area to split comps into two pf: you, them
    # gives you the cash/trade value difference after pct

    def _set_trade_board():
        contr_trde = st.container(border=True)
        #st.session_state['trade'].contr_trde = contr_trde
        contr_trde.write('#### Trade Analyser')

        # print balances
        total_map = {}
        for pfn in pf_names:
            tmp_pct_trade = pct_trade/100 if pfn=='you' else 1
            tmp_df = st.session_state[pfn]['df']
            total = (tmp_df['Price']*tmp_df['Quantity']).sum() * tmp_pct_trade
            _bstr = 'Total' if pfn=='me' else f"Total ({pct_trade}%)"
            contr_trde.write(f"{_bstr} ({pfn.capitalize()}): **${total:.2f}**")
            total_map[pfn] = total

        # print trade balance
        cash_bal = total_map['me'] - total_map['you']
        if cash_bal>1:
            contr_trde.write(f"Balance: **They pay you ${cash_bal:.2f}**")
        elif cash_bal<-1:
            contr_trde.write(f"Balance: **You pay them ${-cash_bal:.2f}**")
        elif (cash_bal<=1) & (cash_bal >= -1):
            contr_trde.write(f"Balance: **Fair Trade**")


    ####################################################################################################################
    # so no error at the beginning
    if ('df' not in st.session_state['me'].keys()) | ('df' not in st.session_state['you'].keys()):
        return

    pf_names = ['me','you']
    tb_p = st.session_state['tabs']['trade']
    pct_trade = st.session_state['trade_pct']
    with tb_p:
        _set_trade_board()
    pass



def compd_custom():
    set_session_state_groups()
    set_scroll2top_button()
    set_sidebar_elements()
    set_tabs()
    set_tbulk()
    set_tcustom(tab_name='me')
    set_tcustom(tab_name='you')
    set_ttrade()
    pass


if __name__ == '__main__':
    # manually enter itms to comp - along with UI(dialogue) to enter hist sale prices
    # clear data butotn
    # bulk mode - common($0.2), reverse($1), custom1(text_box), custom2(text-box)
    # total
    # tabs: bulk, me, you, trade
    # percentage on you total
    compd_custom()

