import streamlit as st
import pandas as pd
import altair as alt

from conf.config import ss_g, hist2days, loc_map
from src.manage_screen_res import set_screen_data, set_screen_contr
from src.common import set_scroll2top_button, set_chrome_driver, write_style_str, reduce_md_spacing, insert_spacer
from src.get_ebayau_listing_data import get_ebayau_listing_data, get_lst_imgs

from compd_desktop import (set_session_state_groups, set_sidebar_elements, set_tabs,
                           show_more_listing_imgs, show_pf_itm_listing)

# page settings
st.set_page_config(page_title="Compd",
                   layout="centered",
                   initial_sidebar_state='expanded',
                   page_icon='./logo/compd_logo_white.png',
                   )


def set_tsearch():
    def _set_stats_board():
        contr_stats = st.container(border=True)
        st.session_state.contr_stats = contr_stats
        contr_stats.write('#### Selected listings:')

    def _set_pchart_container():
        contr_pchart = st.container(border=True)
        st.session_state.contr_pchart = contr_pchart

    def _update_stats_board():
        # df: selected listings, match history param
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst']]
        _dfls = _dfls.loc[_dfls['sold_date'] >= st.session_state['sb']['hist_sdate']]
        num_lsts = len(_dfls)
        if num_lsts > 0:
            stats = {'date_range_str': f"Date range: **{_dfls['sold_date'].min():%d %b %Y} - {_dfls['sold_date'].max():%d %b %Y}**",
                     'listings_str': f"Listings: **{num_lsts}**",
                     'price_range_str': f"Price range: **\${_dfls['price'].min()} - \${_dfls['price'].max()}**",
                     #'last_sold_str': f"Last Sold: {}",
                     'mean_str': f"Mean: **${_dfls['price'].mean():.2f}**",
                     'median_str': f"Median: **${_dfls['price'].median():.2f}**",
                     'dr_start': dfls['sold_date'].min(),
                     'dr_end': dfls['sold_date'].max(),
                     'num_listings': num_lsts,
                     'price_min': _dfls['price'].min(),
                     'price_max': _dfls['price'].max(),
                     'mean': _dfls['price'].mean(),
                     'median': _dfls['price'].median(),
                     }

            contr_stats = st.session_state.contr_stats
            contr_stats.write(stats['date_range_str'])
            contr_stats.write(stats['listings_str'])
            contr_stats.write(stats['price_range_str'])
            contr_stats.write(stats['mean_str'])
            contr_stats.write(stats['median_str'])

            # add price
            contr_stats_p = contr_stats.container(horizontal=True, gap='small', width='content',
                                                  vertical_alignment="top")
            write_style_str(parent_obj=contr_stats_p, str_out='Price: ')
            price_input = contr_stats_p.text_input(label='', label_visibility='collapsed',
                                                   placeholder=f"{stats['mean']:.2f}",
                                                   key="_price_input", width=125)
            # price_input = contr_stats_p.number_input('', min_value=0., value=stats['mean'],
            #                                          label_visibility='collapsed', width=60)
            stats['price'] = price_input

            # save to pf button
            if contr_stats.button('Add to Portfolio'):
                if itm_id not in st.session_state.pf['itms'].keys():
                    st.session_state.pf['itms'][itm_id] = {}
                st.session_state.pf['itms'][itm_id]['dfls'] = _dfls
                st.session_state.pf['itms'][itm_id]['stats'] = stats
                st.toast(f"Saved to Portfolio", icon="✔️")

    def _update_price_chart():
        # df: selected listings, match history param
        _dfls = st.session_state['itms'][itm_id]['dfls']
        _dfls = _dfls.loc[_dfls['include_lst']]
        _dfls = _dfls.loc[_dfls['sold_date'] >= st.session_state['sb']['hist_sdate']]

        contr_pchart = st.session_state.contr_pchart
        if len(_dfls)>1:
            # calc median by date
            price_median = _dfls.groupby('sold_date')['price'].median()
            _dfls['price_median'] = _dfls['sold_date'].map(price_median)

            x_col_name = 'sold_date'
            y_scatter_col_name = 'price'
            y_line_col_name = 'price_median'
            x_axis_min = _dfls[x_col_name].min() - pd.Timedelta(days=1)
            x_axis_max = _dfls[x_col_name].max() + pd.Timedelta(days=1)
            y_axis_min = int(_dfls[y_scatter_col_name].min() * 0.9)
            y_axis_max = int(_dfls[y_scatter_col_name].max() * 1.1)

            x_axis = alt.X(f'{x_col_name}:T', scale=alt.Scale(domain=[x_axis_min, x_axis_max]), title=None)#, axis=alt.Axis(grid=False))
            y_scatter_axis = alt.Y(f'{y_scatter_col_name}:Q', scale=alt.Scale(domain=[y_axis_min, y_axis_max]), title=None, axis=alt.Axis(grid=False))
            y_line_axis = alt.Y(f'{y_line_col_name}:Q', scale=alt.Scale(domain=[y_axis_min, y_axis_max]), title=None, axis=alt.Axis(grid=False))

            line = alt.Chart(_dfls).mark_line(color='blue', size=2,
                                              opacity=0.5,).encode(x=x_axis, y=y_line_axis)
            scatter = alt.Chart(_dfls).mark_point(color='red', size=200,
                                                  filled=False, opacity=0.5,
                                                  strokeWidth=2).encode(x=x_axis, y=y_scatter_axis)
            contr_pchart.altair_chart(scatter + line, use_container_width=True, theme=None)
        else:
            write_style_str(parent_obj=contr_pchart,
                            str_out="Select more listings to generate price chart",
                            color="red", font_size="1em", font_w='bold')

    ####################################################################################################################

    with st.session_state['tabs']['search']:
        # search bar
        sch_phrase = st.text_input(label='',
                                   label_visibility='collapsed',
                                   placeholder='Enter card name and number',
                                   key="sch_phrase_in")
        # manage search bar input
        if len(sch_phrase) == 0:
            # show nothing
            return
        elif len(sch_phrase.split(' '))<2:
            st.write('### Invalid search: enter item name and number')
            return

        # get listing data
        item_loc = st.session_state['sb']['item_loc']
        itm_id = f"{sch_phrase}_{loc_map[item_loc]}"
        if itm_id not in st.session_state['itms'].keys():
            st.session_state['itms'][itm_id] = {}

            ipg = st.session_state['sb']['ipg']
            driver = st.session_state.chrome_driver
            dfls = get_ebayau_listing_data(sch_phrase, item_loc, ipg, driver)
            dfls['include_lst'] = False
            st.session_state['itms'][itm_id]['dfls'] = dfls
            st.session_state['itms'][itm_id]['sch_phrase'] = sch_phrase
            st.session_state['itms'][itm_id]['item_loc'] = item_loc
        else:
            dfls = st.session_state['itms'][itm_id]['dfls']

        # if no data returned
        if len(dfls)==0:
            st.write(f'### No listings returned for: {sch_phrase} - {loc_map[item_loc]}')
            return

        # prep the data to be displayed
        dfls = dfls.loc[dfls['sold_date'] >= st.session_state['sb']['hist_sdate']] # trim to match history param
        if st.session_state['sb']['rm_best_offer']: # remove best offers
            dfls = dfls.loc[dfls['auction_type']!='Best Offer']
        if st.session_state['sb']['show_sltd_lsts']: # show selected listings only
            dfls = dfls.loc[dfls['include_lst']]
            if len(dfls)==0:
                return

        # set some data containers
        if st.session_state['sb']['show_pchart']: # price chart
            _set_pchart_container()
        _set_stats_board() # add container to show price stats

        # display parameters
        c2_img_size = 140

        # display data
        #dfls = dfls.head(5)
        for ix, lst in dfls.iterrows():
            # container - write horizontally
            contr = st.container(border=True)
            contr_1 = contr.container(horizontal=True,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap='small') # select, image

            # select button
            c1_key = f"{itm_id}_{ix}_c1"
            _button_state = contr_1.checkbox(label='',
                                            label_visibility='collapsed',
                                            key=c1_key,
                                            value=lst['include_lst'])
            st.session_state['itms'][itm_id]['dfls'].loc[ix, 'include_lst'] = _button_state

            # show img0
            contr_1.image(f"{lst['img_url0']}/s-l{c2_img_size}.webp", width='content')

            # write vertically now
            contr_2 = contr_1.container(horizontal=False,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap="small")

            # details
            p = lst['price']
            p_str = f"{lst['price_str']}".replace('$',' ') if pd.isnull(p) else f"AU ${lst['price']}"
            write_style_str(parent_obj=contr_2, str_out=f"Sold  {lst['sold_date']:%d %b %Y}", color="#7D615E", font_size="1em")
            write_style_str(parent_obj=contr_2, str_out=lst['title'], color="#000000", font_size="1em", hyperlink=lst['sold_url'])
            strike_thr = True if lst['auction_type']=='Best Offer' else False
            write_style_str(parent_obj=contr_2, str_out=p_str, color="#7D615E", font_size="1.5em", font_w='bold', strike_through=strike_thr)
            write_style_str(parent_obj=contr_2, str_out=lst['auction_type'])
            write_style_str(parent_obj=contr_2, str_out=f"{lst['from_ctry_str']}", color="#7D615E", font_size="1em")

            # show more imgs
            c2_key = f"{itm_id}_{ix}_c2"
            if contr_2.button('show more images', key=c2_key, width='content'):
                show_more_listing_imgs(lst['sold_url'])

            # delete some keys
            delattr(st.session_state, c1_key)
            delattr(st.session_state, c2_key)

        # update containers above
        if st.session_state['sb']['show_pchart']:
            _update_price_chart()
        _update_stats_board()


    pass

def set_tport():
    def _set_portfolio_board():
        contr_pf = st.container(border=True)
        st.session_state.contr_pf = contr_pf
        contr_pf.write('#### Portfolio')

    def _update_portfolio_board():
        dfpf = st.session_state.pf['dfpf']
        if dfpf['include_itm'].sum()>0:
            contr_pf = st.session_state.contr_pf
            total = (dfpf[agg_by]*dfpf['include_itm']).sum()
            contr_pf.write(f"Total: **${total:.2f}**")

            c11 = contr_pf.container(horizontal=True)
            for pct in pcts_c1:
                _str = f"{int(pct*100)}%"
                c11.write(f"{_str}: **${total*pct:.2f}**")

            c22 = contr_pf.container(horizontal=True)
            for pct in pcts_c2:
                _str = f"{int(pct*100)}%"
                c22.write(f"{_str}: **${total*pct:.2f}**")
        pass

    ####################################################################################################################

    # include_itm, , num items, pcts - 90,80,75
    # display portfolio - use most recent lst as photo
    agg_by = 'mean'
    pcts_c1 = [0.9, 0.80, 0.70]
    pcts_c2 = [0.85, 0.75, 0.6]

    # so no error at the beginning
    itm_ids = st.session_state.pf['itms'].keys()
    # st.write(itm_ids)
    # st.write(st.session_state.pf)
    if len(itm_ids)==0:
        return

    # dfpf - itm_id, mean, median,
    dfpf = [pd.Series(st.session_state.pf['itms'][itm_id]['stats']).to_frame(itm_id) for itm_id in itm_ids]
    dfpf = pd.concat(dfpf, axis=1).T
    dfpf['include_itm'] = False
    st.session_state.pf['dfpf'] = dfpf

    tb_p = st.session_state['tabs']['portfolio']
    with tb_p:
        _set_portfolio_board()

        # display itms in pf
        for itm_id, row in dfpf.iterrows():
            stats = st.session_state.pf['itms'][itm_id]['stats']
            dfls = st.session_state.pf['itms'][itm_id]['dfls']

            # container - write horizontally
            contr = st.container(border=True)
            contr_1 = contr.container(horizontal=True,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap='small')

            # select button
            pf_c1_key = f"pf_{itm_id}_c1"
            _button_state = contr_1.checkbox(label='', label_visibility='collapsed', key=pf_c1_key, value=True)
            st.session_state.pf['dfpf'].loc[itm_id, 'include_itm'] = _button_state

            # use first image from dfls
            img_size = '140'
            contr_1.image(f"{dfls['img_url0'].iloc[0]}/s-l{img_size}.webp")

            # write vertically now
            contr_2 = contr_1.container(horizontal=False,
                                      horizontal_alignment="left", vertical_alignment="center",
                                      gap="small")

            sch_phrase = st.session_state['itms'][itm_id]['sch_phrase']
            item_loc = st.session_state['itms'][itm_id]['item_loc']
            contr_2.write(f"{sch_phrase}")
            contr_2.write(f"${row[agg_by]:.2f}")
            contr_2.write(f"{item_loc}")

            # compd itm info
            pf_c3_key = f"pf_{itm_id}_c3"
            if contr_2.button('Show Listings', key=pf_c3_key):
                show_pf_itm_listing(itm_id)

            # delete some keys
            delattr(st.session_state, pf_c1_key)
            delattr(st.session_state, pf_c3_key)

        # update container above
        _update_portfolio_board()
    pass

def set_ttrade():

    with st.session_state['tabs']['trade']:
        contr_you = st.container(horizontal=True,)





def compd_mobile():
    #st.write('compd - mobile')
    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    set_tport()
    pass


if __name__ == '__main__':
    set_scroll2top_button()
    set_chrome_driver()
    set_session_state_groups()
    set_sidebar_elements()
    set_tabs()
    set_tsearch()
    set_tport()
    set_ttrade()
    pass