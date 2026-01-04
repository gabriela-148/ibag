import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np

# -----------------------------
# Variables
# -----------------------------
SHEET_ID = "1gSU91M8C0ssE2oxOKWSPAeWmC8xNo3F1rmBf-SjHYII"
SHEET_NAME = "Sheet1"

# -----------------------------
# Load Data from Google Sheets
# -----------------------------
@st.cache_data(ttl=60)
def load_flights():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(url)

    # Ensure numeric types
    df[['origin_lat', 'origin_lon', 'dest_lat', 'dest_lon', 'burn_rate']] = df[['origin_lat', 'origin_lon', 'dest_lat', 'dest_lon', 'burn_rate']].apply(pd.to_numeric)

    # Calculate distance_km if missing
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # km
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    if 'distance_km' not in df.columns or df['distance_km'].isnull().any():
        df['distance_km'] = df.apply(lambda x: haversine(x.origin_lat, x.origin_lon, x.dest_lat, x.dest_lon), axis=1)

    # Calculate fuel_liters
    if 'fuel_liters' not in df.columns or df['fuel_liters'].isnull().any():
        df['fuel_liters'] = df['distance_km'] * df['burn_rate'] / 100

    return df

flights = load_flights()

# -----------------------------
# Select Flight
# -----------------------------
flight_options = flights.index.tolist()
flight_choice = st.selectbox(
    "Select a Flight", flight_options,
    format_func=lambda x: f"{flights.loc[x, 'origin_iata']} → {flights.loc[x, 'dest_iata']}"
)

flight = flights.loc[flight_choice]

# -----------------------------
# Dashboard Metrics
# -----------------------------
st.title("✈️ Flight Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Origin", flight['origin_iata'])
col2.metric("Destination", flight['dest_iata'])
col3.metric("Distance (km)", f"{flight['distance_km']:.0f}")
col4.metric("Fuel Needed (L)", f"{flight['fuel_liters']:.1f}")

st.metric("Average Ticket Price", f"${flight['avg_ticket_price']:.2f}")

# -----------------------------
# Plot Flight Path
# -----------------------------
fig = go.Figure()

# Flight path
fig.add_trace(go.Scattergeo(
    lon=[flight['origin_lon'], flight['dest_lon']],
    lat=[flight['origin_lat'], flight['dest_lat']],
    mode='lines',
    line=dict(width=2, color='blue'),
    name=f"{flight['origin_iata']} → {flight['dest_iata']}"
))

# Origin & destination points
fig.add_trace(go.Scattergeo(
    lon=[flight['origin_lon'], flight['dest_lon']],
    lat=[flight['origin_lat'], flight['dest_lat']],
    mode='markers',
    marker=dict(size=8, color='red'),
    name="Airports"
))

fig.update_layout(
    geo=dict(
        scope='world',
        projection_type='natural earth',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        countrycolor='rgb(204, 204, 204)',
    ),
    margin={"r":0,"t":0,"l":0,"b":0},
)

st.plotly_chart(fig, use_container_width=True, key=f"flight_map_{flight_choice}")

# -----------------------------
# Additional Flight Details
# -----------------------------
st.subheader("Flight Details")
st.write(f"✈️ Flight from **{flight['origin_iata']}** to **{flight['dest_iata']}**")
st.write(f"💰 Average Ticket Price: ${flight['avg_ticket_price']}")
st.write(f"⛽ Fuel Needed: {flight['fuel_liters']:.1f} L")
st.write(f"🛣️ Distance: {flight['distance_km']:.0f} km")
st.write(f"🔥 Burn Rate: {flight['burn_rate']} L/100km")
