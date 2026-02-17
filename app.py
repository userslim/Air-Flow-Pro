import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- STANDARDS & SPECS (Singapore SS 553) ---
SS_553_MIN_ACH = 20  # Minimum Air Changes per Hour for Hawker Centers
ELECTRICITY_RATE = 0.2911  # SGD per kWh (Q1 2026 SP Group Rate w/ GST)

FAN_SPECS = {
    "HVLS (High Volume Low Speed)": {"wattage": 1500, "cfm": 35000, "radius": 4.0},
    "Standard Ceiling Fan": {"wattage": 80, "cfm": 10000, "radius": 1.0},
    "Industrial Wall Fan": {"wattage": 120, "cfm": 6500, "radius": 0.8}
}

st.set_page_config(page_title="SG Hawker Airflow Sim", layout="wide")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("📍 Building Dimensions")
width = st.sidebar.number_input("Center Width (m)", 5, 100, 30)
length = st.sidebar.number_input("Center Length (m)", 5, 100, 30)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

st.sidebar.header("🌀 Fan Selection")
fan_type = st.sidebar.selectbox("Fan Model", list(FAN_SPECS.keys()))
num_fans = st.sidebar.slider("Number of Fans", 1, 40, 6)

# --- CALCULATIONS ---
total_cfm = num_fans * FAN_SPECS[fan_type]["cfm"]
volume_m3 = width * length * height
volume_ft3 = volume_m3 * 35.3147
ach = (total_cfm * 60) / volume_ft3
total_kw = (num_fans * FAN_SPECS[fan_type]["wattage"]) / 1000
monthly_cost = total_kw * 12 * 30 * ELECTRICITY_RATE # Assuming 12h daily operation

# --- MAIN DASHBOARD ---
st.title("🇸🇬 Hawker Center Airflow & Ventilation Simulation")
st.info("Simulation adheres to **SS 553: Code of Practice for Mechanical Ventilation**.")

col1, col2, col3 = st.columns(3)
col1.metric("Total Airflow", f"{total_cfm:,} CFM")
col2.metric("Calculated ACH", f"{ach:.1f}", delta=f"{ach - SS_553_MIN_ACH:.1f} vs Std")
col3.metric("Est. Monthly Cost", f"${monthly_cost:.2f} SGD")

if ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Warning: Current setup provides {ach:.1f} ACH. SS 553 requires at least {SS_553_MIN_ACH} for food centers.")
else:
    st.success("✅ Compliance: Setup meets or exceeds ventilation requirements.")

# --- AIRFLOW SIMULATION ENGINE ---
def generate_simulation(w, l, n, f_name):
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    
    # Velocity grid
    V = np.zeros_like(X)
    
    # Grid placement for fans
    rows = int(np.sqrt(n))
    cols = (n // rows) + (1 if n % rows != 0 else 0)
    
    r_val = FAN_SPECS[f_name]["radius"]
    strength = FAN_SPECS[f_name]["cfm"] / 8000
    
    for i in range(n):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        # Air velocity decay model
        V += strength * np.exp(-dist / (r_val * 1.5))
    
    return X, Y, V

X, Y, V = generate_simulation(width, length, num_fans, fan_type)

# Plotly Heatmap
fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, width), y=np.linspace(0, length, length),
    colorscale='IceFire', zmin=0, zmax=5,
    colorbar=dict(title="Velocity (m/s)")
))

fig.update_layout(
    title="Predicted Air Velocity Distribution at Table Level (0.5m - 1.2m)",
    xaxis_title="Width (m)", yaxis_title="Length (m)",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
### How to read this simulation:
* **Bright Zones (White/Red):** Areas directly under fans with high velocity (>1.0 m/s).
* **Blue/Dark Zones:** Potential 'Dead Zones' where air is stagnant.
* **Target:** Aim for a consistent light blue/green coverage (0.3 - 0.5 m/s) across the seating area.
""")
