import streamlit as st
from datetime import time
from impl import mcow_analyser
from impl import sbc_tools as sbc
import os
import torch

st.set_page_config(page_title="MCOW: home", page_icon="./static/images/MCOW.png", layout="wide")

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
with st.container(horizontal=True, vertical_alignment="center"):
    st.image("./static/images/MCOW.png", "", 100)
    st.markdown("<p style='color:#4dabf7; font-size: 30px; font-weight:bold; font-family: sans-serif; text-align: center'>MANY COUNTRIES, <br> ONE WORLD PROJECT</p>",
             unsafe_allow_html=True)
     
if "mcow_analyser" not in st.session_state:
    with st.spinner("Wait for it...", show_time=True):
        graph = sbc.load(folder="./impl/data/", format="turtle", filename="country_details_ontology_mejorada.ttl")
        st.session_state.mcow_analyser = mcow_analyser.MCOWAnalyser(graph)

alpha_codes_dict = st.session_state.mcow_analyser.get_alpha_codes_dict()
numerical_attrs_list = st.session_state.mcow_analyser.get_numerical_attributes_list()

st.session_state.alpha_codes_dict = alpha_codes_dict

st.space(size="medium")

col1, col2 = st.columns(2)

show_buttons = False

with col1:
    with st.container(horizontal=False):
            st.markdown("<p style='color: rgb(120 75 27);font-size: 22px; font-family: sans-serif; font-weight:600; max-width: 36vw'>Welcome to the MCOW project! <br>" +
                        " To get started, please select a country from the selector on the right</p>", unsafe_allow_html=True)
            
            st.badge(f"{len(alpha_codes_dict.keys())} countries available!", icon="🌎", color="blue", width="content", help=None)
            st.badge(f"More than {len(numerical_attrs_list)} attributes to analyse!", icon="👨‍🔬", color="orange", width="content", help=None)
            st.badge(f"Historical data from more than 15 years!", icon="📚", color="red", width="content", help=None)

with col2: 
    with st.container(horizontal=True):
        countries = {k.capitalize().replace("-", " "):v for k, v in st.session_state.mcow_analyser.get_countries_dict().items() if k in list(alpha_codes_dict.keys())}
        st.session_state.countries_list = countries
        
        st.space("medium")
        with st.container(horizontal=False):
            #st.markdown("<p style='color:#4dabf7; font-size: 20px; font-family: sans-serif; text-align: center'>MANY COUNTRIES, <br> ONE WORLD PROJECT</p>",
            # unsafe_allow_html=True)
            option = st.selectbox(
                "Let's get started!",
                countries.keys(),
                index=None,
                placeholder="Select a country from the list above",
            )
            st.space("small")
            if option:
                country_wd_code = countries[option]
                alpha_codes_dict_formatted = alpha_codes_dict[option.lower().replace(" ", "-")]
                country_alpha_code = alpha_codes_dict_formatted[0].lower()
                country_continent_class = alpha_codes_dict_formatted[1].title().replace("_Utc", " (and whose time zone is UTC").replace("_", " ") + ")"
                
                st.session_state.country_name = option.capitalize()
                st.session_state.country_wd_code = country_wd_code
                st.session_state.country_alpha_code= country_alpha_code

                with st.container(horizontal=True):
                    col2_1, col2_2, col2_3 = st.columns(3)
                    
                    with col2_2:
                        st.image(f"https://flagcdn.com/224x168/{country_alpha_code}.png", " ", 150)
                    
                st.caption(f"🔎 Small tip: {option.capitalize()} is a country that belongs to {country_continent_class}")
                show_buttons = True

if show_buttons:
    
    st.space("medium")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:

        button1_clicked = st.button(label="Analyse historical tendencies", key="btn_to_hist_tend")

        if button1_clicked:
            st.switch_page("pages/historical_data.py")
    
    with col2:
        button2_clicked = st.button(label="Perform full DAFO analysis", key="btn_to_dafo_anl")
        if button2_clicked:
            st.switch_page("pages/dafo_analysis.py")
            
    with col3:
        button3_clicked = st.button(label="Compare pairs of countries", key="btn_to_country_cmp")
        if button3_clicked:
            st.switch_page("pages/categories_similarity.py")
            
    with col4:
        button4_clicked = st.button(label="Look for another country based on attributes tendencies", key="btn_to_country_hist_tend")
        if button4_clicked:
            st.switch_page("pages/tendency_countries.py")