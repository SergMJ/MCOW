import streamlit as st
import pandas as pd

st.set_page_config(page_title="MCOW: Review the main socio-economic pros and cons of a country", page_icon="./static/images/MCOW.png", layout="wide")

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
        
def enrich_elem(elem):
    if "access" in elem:
        return elem.replace("access", "sanitation access")
    elif "debt" in elem:
        return elem.replace("debt", "public debt rate")
    return elem
# Header
with st.container(horizontal=True, vertical_alignment="center"):
    st.image("./static/images/MCOW.png", "", 100)
    st.markdown("<p style='color:#4dabf7; font-size: 30px; font-weight:bold; font-family: sans-serif; text-align: center'>MANY COUNTRIES, <br> ONE WORLD PROJECT</p>",
             unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    
    with st.container(horizontal=False):
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
                        
            st.session_state.dafo_analysis = st.session_state.mcow_analyser.getDAFOAnalysis(st.session_state.country_wd_code)    
        
        st.space(75)
                
with col2:
    
    if "country_wd_code" in st.session_state:
    
        dafo_strengths = [v.replace("_", " ").capitalize() for v in st.session_state.dafo_analysis["strengths"].values()]
        dafo_weaknesses = [v.replace("_", " ").capitalize() for v in st.session_state.dafo_analysis["weaknesses"].values()]
        
        with st.container(horizontal=False):
            st.header("Country's features analysis", text_alignment="center", anchor=False)
            st.space("small")
        
        
        col2_1, col2_2 = st.columns(2)
        
        with col2_1:
            with st.container(horizontal=False):
                st.markdown("<p style='color: #227229; font-size: 24px; font-family: sans-serif; font-weight:bold; max-width: 36vw; text-decoration: underline;'> Main strengths <br>", unsafe_allow_html=True)
                
                for elem in dafo_strengths:
                    elem = enrich_elem(elem)
                    st.markdown(f"<p style='color: #053609; font-size: 18px; font-family: sans-serif; max-width: 36vw;'> ✔️ {elem}", unsafe_allow_html=True)
        
        with col2_2:
            with st.container(horizontal=False):
                st.markdown("<p style='color: #a10101; font-size: 24px; font-family: sans-serif; font-weight:bold; max-width: 36vw; text-decoration: underline;'> Main weaknesses <br>", unsafe_allow_html=True)
                
                for elem in dafo_weaknesses:
                    elem = enrich_elem(elem)
                    st.markdown(f"<p style='color: #58130f; font-size: 18px; font-family: sans-serif; max-width: 36vw;'> ❌ {elem}", unsafe_allow_html=True)


col1, col2, col3 = st.columns(3)

with col1:
    with st.container(horizontal=True):
        st.space(30)
        button1_clicked = st.button(label="Analyse historical tendencies", key="btn_to_hist_tend")
        if button1_clicked:
            st.switch_page("pages/historical_data.py")
        
with col2:
    with st.container(horizontal=True):
        st.space(30)
        button2_clicked = st.button(label="Compare pairs of countries", key="btn_to_country_cmp", width=250)
        if button2_clicked:
            st.switch_page("pages/categories_similarity.py")
        
with col3:
    with st.container(horizontal=True):
        st.space(30)
        button3_clicked = st.button(label="Look for another country based on attributes tendencies", key="btn_to_country_hist_tend", width=250)
        if button3_clicked:
            st.switch_page("pages/tendency_countries.py")