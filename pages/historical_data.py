import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="MCOW: Take a look at the tendency that an attribute has followed through time", page_icon="./static/images/MCOW.png", layout="wide")

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

countries_list = st.session_state.countries_list
alpha_codes_dict = st.session_state.alpha_codes_dict

def on_country_change():
    if st.session_state.country_selector:
        c = st.session_state.country_selector
        st.session_state.country_name = c
        st.session_state.country_wd_code = countries_list[c]
        st.session_state.country_alpha_code = (
            alpha_codes_dict[c.lower().replace(" ", "-")][0].lower()
        )

if "attr_selector" in st.session_state:
    del st.session_state["attr_selector"]
        
# Header
with st.container(horizontal=True, vertical_alignment="center"):
    st.image("./static/images/MCOW.png", "", 100)
    st.markdown("<p style='color:#4dabf7; font-size: 30px; font-weight:bold; font-family: sans-serif; text-align: center'>MANY COUNTRIES, <br> ONE WORLD PROJECT</p>",
             unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    
    with st.container(horizontal=True):
                    
        st.space("large")
        with st.container(horizontal=False):
            with st.container(horizontal=False):
                st.title(st.session_state.country_name, text_alignment="center", width=350, anchor=False) 
                with st.container(horizontal=True):
                    st.space(85)
                    st.image(f"https://flagcdn.com/224x168/{st.session_state.country_alpha_code}.png", " ", 150)
                
            with st.container(horizontal=True):
                st.space(1)    
                new_option = st.selectbox(
                    "New country selection",
                    label_visibility = "hidden", 
                    options = countries_list.keys(),
                    index=None,
                    key="country_selector",
                    on_change=on_country_change,
                    placeholder="Select another country here!",
                    width=300
                )
                if new_option:
                    
                    new_country_wd_code = countries_list[new_option]
                    alpha_codes_dict_formatted = alpha_codes_dict[new_option.lower().replace(" ", "-")]
                    new_country_alpha_code = alpha_codes_dict_formatted[0].lower()
                    
                    st.session_state.country_name = new_option
                    st.session_state.country_wd_code = new_country_wd_code
                    st.session_state.country_alpha_code = new_country_alpha_code
                        
        st.session_state.temporal_entity_data = st.session_state.mcow_analyser.getTemporalEntityData(st.session_state.country_wd_code)

with col2:
    
    st.space("small")
    
    attr_option = st.selectbox(
    "Looking for tendencies?",
    list(st.session_state.temporal_entity_data.keys()),
    index=None,
    placeholder="Choose one attribute",
    key=f"attr_selector_{st.session_state.country_wd_code}"
)
    
    if attr_option:
        
        values_to_print = st.session_state.temporal_entity_data[attr_option]
        years_list = list()
        values_list = list()
        
        for elem in values_to_print:
            years_list.append(elem[0]) 
            values_list.append(elem[1])
            
        plt.style.use("seaborn-v0_8")
        
        fig, ax = plt.subplots(figsize=(6,2.25))
        ax.set_ylim(min(values_list), max(values_list))
        ax.plot(years_list, values_list, color="brown")
        
        for item in [fig, ax]:
            item.patch.set_visible(False)

        ax.set(xlabel='Years', ylabel='Values',
            title=f'{attr_option.replace("_", " ").capitalize()} evolution')
        ax.grid()
        
        plt.xticks(years_list, years_list)

        st.pyplot(fig)
    
    else:
        st.space(110)
        with st.container(horizontal=True):
            st.space(10)
            st.caption("Fill the selector below to display a graphic of the chosen the historical tendency.", text_alignment="center")
        st.space(110)

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(horizontal=True):
        st.space(30)
        button1_clicked = st.button(label="Compare pairs of countries", key="btn_to_country_cmp", width=250)
        if button1_clicked:
            st.switch_page("pages/categories_similarity.py")
        
with col2:
    with st.container(horizontal=True):
        st.space(30)
        button2_clicked = st.button(label="Look for another country based on attributes tendencies", key="btn_to_country_hist_tend", width=250)
        if button2_clicked:
            st.switch_page("pages/tendency_countries.py")
        
with col3:
    with st.container(horizontal=True):
        st.space(30)
        button3_clicked = st.button(label="Perform full DAFO analysis", key="btn_to_dafo_anl", width=250)
        if button3_clicked:
            st.switch_page("pages/dafo_analysis.py")