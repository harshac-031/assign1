import streamlit as st
import folium
from streamlit_folium import st_folium
import geonamescache

st.title("My Hemisphere Quest")
st.write("Fly to all 4 quarters of the world and collect a stamp in each one!")

# Step 1: load real cities (offline)
gc = geonamescache.GeonamesCache()
countries = gc.get_countries()
cities = [c for c in gc.get_cities().values() if c["population"] >= 1_000_000]

if "stamps" not in st.session_state:
    st.session_state.stamps = {}          # quarter -> where you landed

# Step 2: the two secret numbers
lat = st.slider("Latitude (moves you North / South)", -90.0, 90.0, 0.0)
lon = st.slider("Longitude (moves you East / West)", -180.0, 180.0, 0.0)

# Step 3: which quarter of the world are you in?
if lat >= 0:
    up_down = "North"
else:
    up_down = "South"
if lon >= 0:
    side = "East"
else:
    side = "West"
quarter = up_down + "-" + side
st.success(f"You are in the {quarter} quarter of the world.")

# Step 4: which city is closest to where you landed?
def gap(city):
    return (city["latitude"] - lat) ** 2 + (city["longitude"] - lon) ** 2

near = min(cities, key=gap)
country = countries[near["countrycode"]]
st.write(f"Closest big city: {near['name']}, {country['name']}")

if st.button("Stamp my passport"):
    st.session_state.stamps[quarter] = f"{near['name']}, {country['name']}"

# Step 5: the map
m = folium.Map(location=[20, 0], zoom_start=2, tiles="Esri.WorldImagery")
folium.PolyLine([[0, -180], [0, 180]], color="yellow", tooltip="Equator").add_to(m)
folium.PolyLine([[-90, 0], [90, 0]], color="cyan", tooltip="Prime Meridian").add_to(m)
folium.Marker([lat, lon]).add_to(m)
st_folium(m, height=420, returned_objects=[])

# Step 6: passport and progress
st.progress(len(st.session_state.stamps) / 4, text=f"{len(st.session_state.stamps)} of 4 quarters")
st.dataframe([{"Quarter": k, "Landed near": v} for k, v in st.session_state.stamps.items()])
if len(st.session_state.stamps) == 4:
    st.balloons()
    st.success("You visited all 4 quarters of the world!")
