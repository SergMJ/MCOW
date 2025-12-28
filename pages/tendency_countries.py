import streamlit as st
import pandas as pd
import time
from operator import itemgetter

st.set_page_config(page_title="MCOW: Check out countries that follow the desired tendencies", page_icon="./static/images/MCOW.png", layout="wide")

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

pd.options.display.float_format = "{:,.2f}".format

st.session_state.show_col_2 = True

if "criteria" not in st.session_state:
    st.session_state.criteria = dict()
else:
    st.session_state.show_col_2 = False

@st.dialog("Select the attributes to filter from")
def add_criteria():
    
    attrs_list = ['average_children',
                'economical_growth_rate',
                'inflation_rate',
                'life_expectancy',
                'mortality_rate',
                'natality_rate',
                'population',
                'public_debt_rate',
                'unemployment_rate',
                'youth_unscolarized_percentage']
    
    for attr in attrs_list:
        attr_txt = attr.replace("_", " ").capitalize()
        if attr in st.session_state.criteria:
            opt = st.checkbox(attr_txt, key=attr, value=True)
        else:
            opt = st.checkbox(attr_txt, key=attr)
        
        if opt:
            asc = False
            
            if attr in st.session_state and attr in st.session_state.criteria and st.session_state.criteria[attr] == "i":
                asc = st.toggle("Ascendent tendency", key=attr + "_tend", value=True)
            else:
                asc = st.toggle("Ascendent tendency", key=attr + "_tend")
            
            if asc:
                st.session_state.criteria[attr] = "i"
            else:
                st.session_state.criteria[attr] = "d"
                
        elif attr in st.session_state.criteria:
            del st.session_state.criteria[attr]
    

    if "country_similarity" in st.session_state:
        country_sim = st.checkbox("Use a country to order the results by similarity", key="country_similarity_on", value=True)
        
        if country_sim:
            country = st.selectbox(
                            "New country selection",
                            label_visibility = "hidden", 
                            options = st.session_state.countries_full_list.keys(),
                            index=list(st.session_state.countries_full_list.keys()).index(st.session_state.country_similarity),
                            key="country_selector",
                            placeholder="Select a country",
                            width=200
                        )
            if country:
                st.session_state.country_similarity = country
                
        elif not country_sim or "country_similarity" not in st.session_state:
            del st.session_state["country_similarity"]
        
    else:
        country_sim = st.checkbox("Use a country to order the results by similarity", key="country_similarity_on")
    
        if country_sim:
            country = st.selectbox(
                            "New country selection",
                            label_visibility = "hidden", 
                            options = st.session_state.countries_full_list.keys(),
                            index=None,
                            key="country_selector",
                            placeholder="Select a country",
                            width=200
                        )
            if country:
                st.session_state.country_similarity = country
            
    with st.container(horizontal = False):
        st.space("small")
        
    if st.button("Submit"):
        st.rerun()


# Header
with st.container(horizontal=True, vertical_alignment="center"):
    st.image("./static/images/MCOW.png", "", 100)
    st.markdown("<p style='color:#4dabf7; font-size: 30px; font-weight:bold; font-family: sans-serif; text-align: center'>MANY COUNTRIES, <br> ONE WORLD PROJECT</p>",
             unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    with st.container(horizontal=False):
        st.space("medium")

        with st.container(horizontal=True):
            
            if st.button("Add criteria", key="btn_add_criteria"):
                add_criteria()
                
            st.space("medium")
            
            if st.button("Reset criteria", key="btn_reset_criteria"):
                st.session_state.criteria=dict()
                
                if "country_similarity" in st.session_state:
                    del st.session_state["country_similarity"]
                st.rerun()
        
        st.space(2)
        
        with st.container(horizontal=True):
            st.space("medium")
            with st.container(horizontal=False):
                if st.button("👓 Search countries", key="btn_search_by_criteria"):
                    with st.spinner("Computing similarities..."):
                        st.session_state.similar_countries = st.session_state.mcow_analyser.multi_analyse_graph_values(st.session_state.criteria)
                        #calculate_countries_similarity
                        if "country_similarity" in st.session_state:
                            selected_country = st.session_state.countries_full_list[st.session_state.country_similarity]
                            
                            similarity_order_query = list()
                            similarity_order_query.append(selected_country)
                            
                            for country_name in st.session_state.similar_countries[0].keys():
                                formatted_country = country_name.replace("-", " ").capitalize()
                                country_wd_code = st.session_state.countries_full_list[formatted_country]
                                similarity_order_query.append(country_wd_code)
                            
                            similarity_matrix, valid_countries, embeddings = st.session_state.mcow_analyser.calculate_countries_similarity(similarity_order_query)
                            
                            st.session_state.similar_countries_full_list = list(st.session_state.similar_countries[0].keys())
                            st.session_state.similarity_matrix = similarity_matrix
                        
                    st.session_state.show_col_2 = True

        st.markdown(f"<p style='color:#69594c; font-size: 26px; font-family: sans-serif; font-weight: 600; margin-top: 30px;'>Selected criteria:</p>", unsafe_allow_html=True)
        
        if len(st.session_state.criteria)>0:
            for k,v in st.session_state.criteria.items():
                k = k.replace("_", " ").capitalize()
                if v == "i":
                    st.markdown(f"<p style='color:#686868; font-size: 18px; font-family: sans-serif; padding-left: 1rem'>⬆️ {k}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#686868; font-size: 18px; font-family: sans-serif; padding-left: 1rem'>⬇️ {k}</p>", unsafe_allow_html=True)
                    
            if "country_similarity" in st.session_state:
                        selected_country = st.session_state.country_similarity
                        st.write(f"(Ordered by similarity with {selected_country})")
            
            st.space(40)
            
        else:
            st.space(40)
            st.caption("Add some attributes to look for countries that fulfills them.")
            st.space("small")

with col2:
    
    st.space("medium")
    
    if st.session_state.show_col_2 and "similar_countries" in st.session_state:
        similar_countries = st.session_state.similar_countries
        
        if len(similar_countries[0]) == 0:
            with st.container(horizontal=False):
                st.space("large")
                st.markdown(f"<p style='font-size: 28px; font-family: sans-serif; text-align: center; margin-right: 10%;'>No matches found. <br>" + 
                            "Choose a different combination and try again!</p>", unsafe_allow_html=True)
                st.title("")
        else:
            attr_list = list(st.session_state.criteria.keys())
            print_data = dict()
            
            for country, rates_and_values_lst in similar_countries[1].items():
                formatted_country = country.replace("-", " ").capitalize()
                for ratio_and_value in rates_and_values_lst:
                    for ratio, value in ratio_and_value.items():
                        ratio = ratio.replace("_", " ").capitalize()
                        if ratio not in print_data:
                            print_data[ratio] = dict()
                            
                        print_data[ratio][formatted_country] = value
            
            country_count = len(list(similar_countries[1].keys()))
            height = "auto" if country_count < 8 else 300
                                 
            if "country_similarity" in st.session_state:
                fulfilled_conditions_countries_names = list(similar_countries[0].keys())
                similarities_vector = st.session_state.similarity_matrix[0]             # Only the first row (similarities with the selected country) is needed
                country_name_similarity_dict = dict()
                
                for i in range(1, len(similarities_vector)):
                    country_name = fulfilled_conditions_countries_names[i-1]
                    country_name_similarity_dict[country_name] = float(similarities_vector[i])
                
                ordered_countries_dict = dict(reversed(sorted(country_name_similarity_dict.items(), key=itemgetter(1))))
                print_data_with_similarity = dict()
                
                for k, v in print_data.items():
                    print_data_with_similarity[k] = dict()

                    for country, sim in ordered_countries_dict.items():
                        country_formatted = country.replace("-", " ").capitalize()
                        print_data_with_similarity[k][country_formatted] = print_data[k][country_formatted]
                
                df = pd.DataFrame(print_data_with_similarity)
                st.dataframe(df.round(2), height=height)
            
            else:
                df = pd.DataFrame(print_data)
                st.dataframe(df.round(2), height=height)

st.space("small")
    
col1, col2, col3= st.columns(3)

with col1:
    with st.container(horizontal=True):
        st.space(30)
        button1_clicked = st.button(label="Analyse historical tendencies", key="btn_to_hist_tend")

        if button1_clicked:
            st.switch_page("pages/historical_data.py")

with col2:
    with st.container(horizontal=True):
        st.space(30)
        button2_clicked = st.button(label="Perform full DAFO analysis", key="btn_to_dafo_anl")
        if button2_clicked:
            st.switch_page("pages/dafo_analysis.py")
        
with col3:
    with st.container(horizontal=True):
        st.space(30)
        button3_clicked = st.button(label="Compare pairs of countries", key="btn_to_country_cmp")
        if button3_clicked:
            st.switch_page("pages/categories_similarity.py")