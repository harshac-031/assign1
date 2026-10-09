import streamlit as st
import folium
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium
import geonamescache

st.title("My Passport Map: Collect Pins Around the World!")
st.write("Your mission: land near a big city on **all 6 continents** and collect a passport stamp from each. "
         "Move the sliders, or just click on the map to drop your pin!")

# Step 1: load real cities (offline)
gc = geonamescache.GeonamesCache()
countries = gc.get_countries()
cities = [c for c in gc.get_cities().values() if c["population"] >= 1_000_000]
continents = {"AS": "Asia", "AF": "Africa", "EU": "Europe",
              "NA": "North America", "SA": "South America", "OC": "Oceania"}
pin_colours = ["red", "blue", "green", "orange", "purple", "darkred", "teal", "magenta", "brown", "navy"]

# Step 2: things the app must remember between clicks
if "stamps" not in st.session_state:
    st.session_state.stamps = []                       # one entry for every stamp you collect
pin_start = st.session_state.get("pin_start", (0.0, 0.0))   # where the last map click put the pin

# Step 3: who is the explorer? (your name goes in the passport)
name = st.text_input("Your name", placeholder="Type your name here")
if name == "":
    name = "Explorer"

# Step 4: the two secret numbers (they start where you last clicked on the map)
lat = st.slider("Latitude (moves you North / South)", -90.0, 90.0, pin_start[0])
lon = st.slider("Longitude (moves you East / West)", -180.0, 180.0, pin_start[1])

# Step 5: which city is closest to where you landed?
def gap(city):
    return (city["latitude"] - lat) ** 2 + (city["longitude"] - lon) ** 2

near = min(cities, key=gap)
country = countries[near["countrycode"]]
on_land = gap(near) ** 0.5 < 8                         # farther than 8 degrees = nothing nearby

if on_land:
    st.success(f"{name}, you landed near {near['name']}, {country['name']}!")
    if st.button("Stamp my passport"):
        stamp = {"place": f"{near['name']}, {country['name']}", "continent": continents[country["continentcode"]],
                 "lat": lat, "lon": lon}
        if stamp not in st.session_state.stamps:       # no double stamp for the same spot
            st.session_state.stamps.append(stamp)
else:
    st.warning("Splash! Open ocean or empty wilderness. Try different numbers!")

# Step 6: the map. Every stamp keeps its own coloured, numbered pin.
m = folium.Map(location=[20, 0], zoom_start=2, min_zoom=1, max_bounds=True, tiles=None)   # one world only, no repeats
folium.TileLayer("Esri.WorldImagery", no_wrap=True, bounds=[[-90, -180], [90, 180]]).add_to(m)
folium.PolyLine([[0, -180], [0, 180]], color="yellow", tooltip="Equator").add_to(m)
folium.PolyLine([[-90, 0], [90, 0]], color="cyan", tooltip="Prime Meridian").add_to(m)

for number, stamp in enumerate(st.session_state.stamps):
    colour = pin_colours[number % len(pin_colours)]    # every stamp gets the next colour in the list
    pin = BeautifyIcon(number=number + 1, icon_shape="marker", background_color=colour,
                       border_color="white", text_color="white")
    folium.Marker([stamp["lat"], stamp["lon"]], icon=pin, tooltip=f"Stamp {number + 1}: {stamp['place']}").add_to(m)

# your plane sits on its own layer, so the map does not reload when you move
pin_layer = folium.FeatureGroup()
folium.Marker([lat, lon], icon=folium.Icon(color="gray", icon="plane", prefix="fa"), tooltip="You are here").add_to(pin_layer)
map_click = st_folium(m, width=700, height=420, feature_group_to_add=pin_layer, returned_objects=["last_clicked"])["last_clicked"]

# Step 7: a click on the map moves the sliders and the plane
if map_click and map_click != st.session_state.get("last_click"):
    st.session_state.last_click = map_click
    new_lat = round(map_click["lat"], 2)
    new_lon = round((map_click["lng"] + 180) % 360 - 180, 2)   # keep longitude between -180 and 180
    st.session_state.pin_start = (new_lat, new_lon)
    st.rerun()

# Step 8: keep your map! (a screenshot, or download it with all your coloured pins)
st.caption("Take a screenshot: press Windows + Shift + S (Windows) or Command + Shift + 4 (Mac).")
st.download_button("Download my map", m.get_root().render(), file_name="my_world_map.html", mime="text/html")

# Step 9: the passport
st.subheader(f"{name}'s Passport")
visited = {stamp["continent"] for stamp in st.session_state.stamps}
st.progress(len(visited) / 6, text=f"{len(visited)} of 6 continents")
st.dataframe([{"No.": number + 1, "Pin colour": pin_colours[number % len(pin_colours)], "Explorer": name,
               "Landed near": stamp["place"], "Continent": stamp["continent"]}
              for number, stamp in enumerate(st.session_state.stamps)])
if len(visited) == 6:
    st.balloons()
    st.success(f"Well done, {name}! You travelled the whole world using only numbers! "
               "Every dot on a map is just latitude + longitude.")
