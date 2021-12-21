import json
import streamlit as st
import pandas as pd
import os
import postcodes_io_api
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim


st.title("List of schools")

countries = ["Australia", "New Zealand", "United Kingdom", "Wales"]

api  = postcodes_io_api.Api(debug_http=False)
tf = TimezoneFinder()
geoLoc = Nominatim(user_agent="GetLoc")


@st.cache 
def get_lat_long_from_postcode(postcode):
    postcode_info = api.get_postcode(postcode)
    lat = postcode_info["result"]["latitude"]
    long = postcode_info["result"]['longitude']
    return lat, long

@st.cache
def get_address_from_location(lat, long):
    try:
        locname = geoLoc.reverse(f"{lat}, {long}")    
        return locname.address
    except Exception as e:
        print(e)
        return "No address found"

@st.cache
def get_timezone(lat, long):
    try:
        return tf.timezone_at(lng=float(long), lat=float(lat))
    except:
        return "No timezone found"



@st.cache
def get_schools_AU():
    with st.spinner('Waiting...'):
        if os.path.exists("schools_AU.pkl"):
            return pd.read_pickle("schools_AU.pkl")

        data = pd.read_excel("schools.xlsx", sheet_name='Australia')
        data.rename(columns = {'Latitude':'latitude', 'Longitude':'longitude'}, inplace = True)
        data['Address'] = data.apply(lambda row: get_address_from_location(row['latitude'], row['longitude']), axis=1)
        data['Timezone'] = data.apply(lambda row: get_timezone(row['latitude'], row['longitude']), axis=1)
        data.to_pickle("schools_AU.pkl")
        return data

@st.cache
def get_schools_NZ():
    with st.spinner('Waiting...'):

        if os.path.exists("schools_NZ.pkl"):
            return pd.read_pickle("schools_NZ.pkl")

        data = pd.read_excel("schools.xlsx", sheet_name='New Zealand')
        data.rename(columns = {'Latitude':'latitude', 'Longitude':'longitude', "Org_Name": "School Name", "Add1_City": "State", "Add2_Suburb": "Suburb"}, inplace = True)
        data['Address'] = data.apply(lambda row: get_address_from_location(row['latitude'], row['longitude']), axis=1)
        data['Timezone'] = data.apply(lambda row: get_timezone(row['latitude'], row['longitude']), axis=1)
        data.to_pickle("schools_NZ.pkl")
        return data

@st.cache
def get_schools_UK():
    with st.spinner('Waiting...'):

        if os.path.exists("schools_UK.pkl"):
            data =  pd.read_pickle("schools_UK.pkl")
            return data 

        data = pd.read_excel("schools.xlsx", sheet_name='United Kingdom', )
        data.rename(columns = { "Establishment name": "School Name", "Region": "State", "Local authority (name)": "Suburb"}, inplace = True)

        latitudes = []
        longitudes = []
        addresses = []
        timezones = []

        def chunk(seq, size):
            return (seq[pos:pos + size] for pos in range(0, len(seq), size))
        
        for i, postcode_chunk in enumerate(chunk(data['Postcode'], 50)):
            print(i*50)
            postcodes = api.get_bulk_postcodes(list(postcode_chunk))

            for postcode in postcodes['result']:

                if not postcode['result']:
                    latitudes.append(0)
                    longitudes.append(0)
                    addresses.append("No address found")
                    timezones.append("No timezone found")
                else:
                    latitudes.append(postcode["result"]["latitude"])
                    longitudes.append(postcode["result"]["longitude"])
                    addresses.append(get_address_from_location(postcode["result"]["latitude"], postcode["result"]["longitude"]))
                    timezones.append(get_timezone(postcode["result"]["latitude"], postcode["result"]["longitude"]))

        data['latitude'] = latitudes
        data['longitude'] = longitudes
        data['Address'] = addresses
        data['Timezone'] = timezones
        
        data.to_pickle("schools_UK.pkl")
        return data



@st.cache
def get_schools_Wales():
    with st.spinner('Waiting...'):

        if os.path.exists("schools_Wales.pkl"):
            return  pd.read_pickle("schools_Wales.pkl")


        data = pd.read_excel("schools.xlsx", sheet_name='Wales', )
        data.rename(columns = { "School Name": "School Name", "Local Authority": "Suburb"}, inplace = True)

        data.to_pickle("schools_Wales.pkl")
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

elif country == "Wales":
    schools = get_schools_Wales()
    state_label = "Local authority"


st.markdown(f"There are *{len(schools)}* in **{country}** schools to choose from.")

school = st.sidebar.selectbox("Schools", options = schools[["School Name"]])
schools_by_name = schools[schools["School Name"] == school]
states = schools_by_name['State']
state = st.sidebar.selectbox(state_label, options = list(states), index=0)

suburbs = schools_by_name[schools_by_name['State'] == state]

suburb = st.sidebar.selectbox("Suburb", options = list(suburbs["Suburb"]))

result = suburbs[suburbs["Suburb"] == suburb]

if  country == "United Kingdom":
    try:  
        result['Address'] = get_address_from_location(
            float(result["latitude"].astype(float)), float(result["longitude"].astype(float)))
    except:
        result['Address'] = "No address found"

elif country == 'Wales':
    location = get_lat_long_from_postcode(result["Postcode"].values[0])

    if location:
        result['latitude'] = location[0]
        result['longitude'] = location[1]
        result['Address'] = get_address_from_location(location[0], location[1])
        result['timezone'] = tf.timezone_at(lng=location[1], lat=float(location[0]))

# result
# st.markdown(result.Address.values[0])
st.markdown(f"**{result['School Name'].values[0]}**")
st.json(result.to_json(orient="records"))

try:
    st.map(result)
except:
    pass
