import json
import streamlit as st
import pandas as pd
import os
import postcodes_io_api

st.title("List of schools")

countries = ["Australia", "New Zealand", "United Kingdom"]


@st.cache
def get_schools_AU():
    with st.spinner('Waiting...'):
        if os.path.exists("schools_AU.pkl"):
            return pd.read_pickle("schools_AU.pkl")

        data = pd.read_excel("schools.xlsx", sheet_name='Australia')
        data.rename(columns = {'Latitude':'latitude', 'Longitude':'longitude'}, inplace = True)
        data.to_pickle("schools_AU.pkl")
        return data

@st.cache
def get_schools_NZ():
    with st.spinner('Waiting...'):

        if os.path.exists("schools_NZ.pkl"):
            return pd.read_pickle("schools_NZ.pkl")

        data = pd.read_excel("schools.xlsx", sheet_name='New Zealand')
        data.rename(columns = {'Latitude':'latitude', 'Longitude':'longitude', "Org_Name": "School Name", "Add1_City": "State", "Add2_Suburb": "Suburb"}, inplace = True)
        data.to_pickle("schools_NZ.pkl")
        return data

@st.cache
def get_schools_UK():
    with st.spinner('Waiting...'):

        if os.path.exists("schools_UK.pkl"):
            return pd.read_pickle("schools_UK.pkl")

        data = pd.read_excel("schools.xlsx", sheet_name='United Kingdom', )
        data.rename(columns = { "Establishment name": "School Name", "Region": "State", "Local authority (name)": "Suburb"}, inplace = True)
        data.to_pickle("schools_UK.pkl")
        return data

country = st.sidebar.selectbox("Countries", sorted(countries))


if country == "Australia":
    schools = get_schools_AU()
    state_label = 'State'

elif country == "New Zealand":
    schools = get_schools_NZ()
    state_label = 'City'

elif country == "United Kingdom":
    schools = get_schools_UK()
    state_label = "Region"

st.markdown(f"There are *{len(schools)}* in **{country}** schools to choose from.")

school = st.sidebar.selectbox("Schools", options = schools[["School Name"]])
schools_by_name = schools[schools["School Name"] == school]
states = schools_by_name['State']
state = st.sidebar.selectbox(state_label, options = list(states), index=0)

suburbs = schools_by_name[schools_by_name['State'] == state]

suburb = st.sidebar.selectbox("Suburb", options = list(suburbs["Suburb"]))

result = suburbs[suburbs["Suburb"] == suburb]
result

api  = postcodes_io_api.Api(debug_http=False)


if  country == "United Kingdom":
    try:  
        postcode = api.get_postcode(result["Postcode"].values[0])
        result["latitude"] = postcode["result"]["latitude"]
        result["longitude"] = postcode["result"]["longitude"]
    except:
        result["latitude"] = 0.0
        result["longitude"] = 0.0
try:
    st.map(result)
except:
    pass


