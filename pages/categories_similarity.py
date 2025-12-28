import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards 

st.set_page_config(page_title="MCOW: Analyse countries similarity by categories", page_icon="./static/images/MCOW.png", layout="wide")

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

countries_list = st.session_state.countries_list
alpha_codes_dict = st.session_state.alpha_codes_dict

def on_country_one_change():
    if st.session_state.country_one_selector:
        c = st.session_state.country_one_selector
        st.session_state.country_one_name = c
        st.session_state.country_one_wd_code = countries_list[c]
        st.session_state.country_one_alpha_code = (
            alpha_codes_dict[c.lower().replace(" ", "-")][0].lower()
        )

def on_country_two_change():
    if st.session_state.country_two_selector:
        c = st.session_state.country_two_selector
        st.session_state.country_two_name = c
        st.session_state.country_two_wd_code = countries_list[c]
        st.session_state.country_two_alpha_code = (
            alpha_codes_dict[c.lower().replace(" ", "-")][0].lower()
        )

def get_similarity_percent(value):
    return str(round(max(value,0)*100, 1)) + "%"    # It does not make any sense to have negative similarities due to negative values.

def get_tooltip_text(dictionary):
    sorted_dict = {key: value for key, value in sorted(dictionary.items(), key=lambda item: item[1])}
    values_list = list(sorted_dict.keys())
    
    tooltip_text = "The most similar features within these countries are:"
    
    for i in range(min(3, len(values_list))):
        cur_text = values_list[-i].replace("_", " ").capitalize()
        
        if "years" in cur_text:
            cur_text = "Population from " + cur_text
        
        tooltip_text += f"\n{i+1}. {cur_text}"
    
    return tooltip_text

# Header
with st.container(horizontal=True, vertical_alignment="center"):
    st.image("./static/images/MCOW.png", "", 100)
    st.markdown("<p style='color:#4dabf7; font-size: 30px; font-weight:bold; font-family: sans-serif; text-align: center'>MANY COUNTRIES, <br> ONE WORLD PROJECT</p>",
             unsafe_allow_html=True)
    
col1, col2 = st.columns(2)

with col1:
    
    col1_1, col1_2 = st.columns(2)
    
    with st.container(horizontal=True):
                    
        with st.container(horizontal=False, height="content"):
            if "country_one_name" in st.session_state:
                st.title(st.session_state.country_one_name, text_alignment="center", width=250, anchor=False) 
                with st.container(horizontal=True):
                    st.space(24)
                    st.image(f"https://flagcdn.com/224x168/{st.session_state.country_one_alpha_code}.png", " ", 150)
            else:
                st.title(st.session_state.country_name, text_alignment="center", width=250, anchor=False) 
                with st.container(horizontal=True):
                    st.space(24)
                    st.image(f"https://flagcdn.com/224x168/{st.session_state.country_alpha_code}.png", " ", 150)
            
            new_option = st.selectbox(
                "New country selection 1",
                label_visibility = "hidden", 
                options = countries_list.keys(),
                index=None,
                key="country_one_selector",
                on_change=on_country_one_change,
                placeholder="Select the first country",
                width=225
            )
            if new_option:
                
                new_country_wd_code = countries_list[new_option]
                alpha_codes_dict_formatted = alpha_codes_dict[new_option.lower().replace(" ", "-")]
                new_country_alpha_code = alpha_codes_dict_formatted[0].lower()
                
                st.session_state.country_one_name = new_option
                st.session_state.country_one_wd_code = new_country_wd_code
                st.session_state.country_one_alpha_code = new_country_alpha_code

        with st.container(horizontal=False):
            if "country_two_name" in st.session_state:
                st.title(st.session_state.country_two_name, text_alignment="center", width=250, anchor=False) 
                with st.container(horizontal=True):
                    st.space(24)
                    st.image(f"https://flagcdn.com/224x168/{st.session_state.country_two_alpha_code}.png", " ", 150)
            else:
                st.title(st.session_state.country_name, text_alignment="center", width=250, anchor=False) 
                with st.container(horizontal=True):
                    st.space(24)
                    st.image(f"https://flagcdn.com/224x168/{st.session_state.country_alpha_code}.png", " ", 150)
              
            new_option = st.selectbox(
                "New country selection 2",
                label_visibility = "hidden", 
                options = countries_list.keys(),
                index=None,
                key="country_two_selector",
                on_change=on_country_two_change,
                placeholder="Select the second country",
                width=225
            )
            if new_option:
                
                new_country_wd_code = countries_list[new_option]
                alpha_codes_dict_formatted = alpha_codes_dict[new_option.lower().replace(" ", "-")]
                new_country_alpha_code = alpha_codes_dict_formatted[0].lower()
                
                st.session_state.country_two_name = new_option
                st.session_state.country_two_wd_code = new_country_wd_code
                st.session_state.country_two_alpha_code = new_country_alpha_code

with col2:
    
    with st.container(horizontal=True):
        st.space("medium")
    
        if "country_one_name" in st.session_state and "country_two_name" in st.session_state:
            with st.spinner("Calculating similarity...", show_time=True):
                st.session_state.demographic_attrs = st.session_state.mcow_analyser.getAttributesSimilarity(st.session_state.country_one_wd_code, st.session_state.country_two_wd_code, "d")
                st.session_state.economical_attrs = st.session_state.mcow_analyser.getAttributesSimilarity(st.session_state.country_one_wd_code, st.session_state.country_two_wd_code, "e")
                st.session_state.social_attrs = st.session_state.mcow_analyser.getAttributesSimilarity(st.session_state.country_one_wd_code, st.session_state.country_two_wd_code, "s")
                st.session_state.territorial_attrs = st.session_state.mcow_analyser.getAttributesSimilarity(st.session_state.country_one_wd_code, st.session_state.country_two_wd_code, "t")

            total_demographic_similarity_value = st.session_state.demographic_attrs["total"]
            total_demographic_similarity = get_similarity_percent(total_demographic_similarity_value)
            demographic_values_dict = st.session_state.demographic_attrs["values_dict"]
            demographic_tooltip_text = get_tooltip_text(demographic_values_dict) if total_demographic_similarity_value > 0 else "These countries are completely oppossite on demographic terms."
            
            total_economical_similarity_value = st.session_state.economical_attrs["total"]
            total_economical_similarity = get_similarity_percent(total_economical_similarity_value)
            economical_values_dict = st.session_state.economical_attrs["values_dict"]
            economical_tooltip_text = get_tooltip_text(economical_values_dict) if total_economical_similarity_value > 0 else "These countries are completely oppossite on economical terms."
            
            total_social_similarity_value = st.session_state.social_attrs["total"]
            total_social_similarity = get_similarity_percent(total_social_similarity_value)
            social_values_dict = st.session_state.social_attrs["values_dict"]
            social_tooltip_text = get_tooltip_text(social_values_dict) if total_social_similarity_value > 0 else "These countries are completely oppossite on social terms."
            
            total_territorial_similarity = get_similarity_percent(st.session_state.territorial_attrs["total"])
            territorial_lcs = st.session_state.territorial_attrs["lcs"]
            territorial_tooltip_text = f"Both countries belong to the category '{territorial_lcs.replace("_", " ").capitalize()}'"
            
            if "continent_density_classification" in territorial_lcs:
                territorial_tooltip_text = "The countries do not seem to belong to a common category."
            
            
            with st.container(horizontal=False):
                
                st.space(25)
                col2_1, col_2_2 = st.columns(2)
                
             
                with col2_1:
                    with st.container(horizontal=False):
                        st.metric("Demographic similarity", total_demographic_similarity, help=demographic_tooltip_text, width=250, border=True)
                        st.space("medium")
                        st.metric("Economical similarity", total_economical_similarity, help=economical_tooltip_text, width=250, border=True)
                    
                    with col_2_2:
                        
                        with st.container(horizontal=False):
                            st.metric("Social similarity", total_social_similarity, help=social_tooltip_text, width=250, border=True)
                            st.space("medium")
                            st.metric("Territorial similarity", total_territorial_similarity, help=territorial_tooltip_text, width=250, border=True)
                        
                        style_metric_cards(background_color="#ffe5d7", border_left_color="#e1b09a", border_radius_px=10)
        
        else:
            with st.container(horizontal=False):
                st.space(165)
                with st.container(horizontal=True):
                    st.space(10)
                    st.caption("Chose two countries to check out their similarities.", text_alignment="center")
                st.space(165)

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
        button2_clicked = st.button(label="Perform full DAFO analysis", key="btn_to_dafo_anl", width=250)
        if button2_clicked:
            st.switch_page("pages/dafo_analysis.py")
        
with col3:
    with st.container(horizontal=True):
        st.space(30)
        button3_clicked = st.button(label="Look for another country based on attributes tendencies", key="btn_to_country_hist_tend", width=250)
        if button3_clicked:
            st.switch_page("pages/tendency_countries.py")