import streamlit as st
import numpy as np


# --- STANDARDS & SPECS (Singapore SS 553) ---
SS_553_MIN_ACH = 20  # Minimum Air Changes per Hour for Eating Houses
SP_GROUP_RATE = 0.2988  # SGD per kWh (Typical SG rate)

FAN_SPECS = {
    "HVLS (High Volume Low Speed)": {"wattage": 1500, "cfm": 35000, "radius": 4.5},
    "Standard Ceiling Fan": {"wattage": 75, "cfm": 10000, "radius": 1.2},
    "Wall Mount Fan": {"wattage": 60, "cfm": 5000, "radius": 0.8}
}

st.set_page_config(page_title="SG Hawker Airflow Sim", layout="wide")

# --- UI SIDEBAR ---
st.sidebar.header("📍 Layout Dimensions")
width = st.sidebar.number_input("Center Width (m)", 5, 100, 30)
length = st.sidebar.number_input("Center Length (m)", 5, 100, 40)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

st.sidebar.header("🌀 Fan Configuration")
fan_type = st.sidebar.selectbox("Select Fan Type", list(FAN_SPECS.keys()))
num_fans = st.sidebar.slider("Number of Fans", 1, 30, 6)

# --- CALCULATIONS & COMPLIANCE ---
volume_m3 = width * length * height
volume_ft3 = volume_m3 * 35.3147
total_cfm = num_fans * FAN_SPECS[fan_type]["cfm"]
ach = (total_cfm * 60) / volume_ft3

# --- MAIN DASHBOARD ---
st.title("🇸🇬 Hawker Center Airflow & Ventilation Simulator")
st.markdown(f"**Standard Check:** SS 553 recommends ~{SS_553_MIN_ACH} ACH for food centers.")

col1, col2, col3 = st.columns(3)
col1.metric("Total Airflow", f"{total_cfm:,} CFM")
col2.metric("Calculated ACH", f"{ach:.1f}", delta=f"{ach - SS_553_MIN_ACH:.1f} vs Std")
col3.metric("Daily Energy Cost", f"S${(num_fans * FAN_SPECS[fan_type]['wattage'] * 12 / 1000 * SP_GROUP_RATE):.2f}")

if ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Low Ventilation: Below SS 553 standard of {SS_553_MIN_ACH} ACH. Add more fans or switch to HVLS.")
else:
    st.success("✅ Compliance: Setup meets or exceeds mechanical ventilation standards.")

# --- PHYSICS SIMULATION ENGINE ---
def simulate_airflow(w, l, n, f_name):
    # Create grid
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)
    
    # Place fans in a grid pattern
    rows = int(np.sqrt(n))
    cols = (n // rows) + (1 if n % rows != 0 else 0)
    
    r_eff = FAN_SPECS[f_name]["radius"]
    strength = FAN_SPECS[f_name]["cfm"] / 10000 
    
    for i in range(n):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        # Velocity decay logic
        V += strength * np.exp(-dist / (r_eff * 1.5))
    
    return X, Y, V

X, Y, V = simulate_airflow(width, length, num_fans, fan_type)

# Plotly Heatmap
fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, width), y=np.linspace(0, length, length),
    colorscale='Viridis', zmin=0, zmax=5,
    colorbar=dict(title="Velocity (m/s)")
))

fig.update_layout(
    title="Predicted Air Velocity Distribution (Floor Level)",
    xaxis_title="Width (m)", yaxis_title="Length (m)", height=600
)

st.plotly_chart(fig, use_container_width=True)

