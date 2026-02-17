import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION & SS 553 STANDARDS ---
SS_553_MIN_ACH = 20  
FAN_TYPES = {
    "HVLS (High Volume Low Speed)": {"wattage": 1500, "cfm": 35000, "radius": 3.5}, # ~7m diameter
    "Standard Ceiling Fan": {"wattage": 80, "cfm": 10000, "radius": 0.8},
    "Wall Mount Fan": {"wattage": 60, "cfm": 5000, "radius": 0.5}
}

st.set_page_config(page_title="SG Hawker Airflow Sim", layout="wide")

## UI SIDEBAR
st.sidebar.header("📍 Layout Settings")
width = st.sidebar.number_input("Center Width (m)", 10, 100, 30)
length = st.sidebar.number_input("Center Length (m)", 10, 100, 30)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

st.sidebar.header("🌀 Fan Configuration")
fan_choice = st.sidebar.selectbox("Select Fan Type", list(FAN_TYPES.keys()))
num_fans = st.sidebar.slider("Number of Fans", 1, 30, 4)
fan_wattage = st.sidebar.number_input("Fan Wattage (W)", 1, 5000, FAN_TYPES[fan_choice]["wattage"])

# --- PHYSICS ENGINE (Simplified 2D Velocity Field) ---
def simulate_airflow(w, l, n_fans, f_type):
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    
    velocity = np.zeros_like(X)
    
    # Simple grid placement for fans
    rows = int(np.sqrt(n_fans))
    cols = (n_fans // rows) + (1 if n_fans % rows != 0 else 0)
    
    fan_r = FAN_TYPES[f_type]["radius"]
    strength = FAN_TYPES[f_type]["cfm"] / 10000 
    
    for i in range(n_fans):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        
        # Calculate distance-based decay
        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        # SS 553 logic: Air velocity is highest under the fan and decays radially
        velocity += strength * np.exp(-dist / (fan_r * 1.5))

    return X, Y, velocity

# --- MAIN DASHBOARD ---
st.title("🇸🇬 Hawker Center Airflow Simulator")
st.markdown(f"**Compliance Target (SS 553):** `{SS_553_MIN_ACH} ACH` for Markets/Food Centers.")

# Calculations
total_cfm = num_fans * FAN_TYPES[fan_choice]["cfm"]
volume_ft3 = (width * length * height) * 35.3147 
calc_ach = (total_cfm * 60) / volume_ft3

c1, c2, c3 = st.columns(3)
c1.metric("Total Airflow", f"{total_cfm:,} CFM")
c2.metric("Calculated ACH", f"{calc_ach:.1f}", delta=f"{calc_ach - SS_553_MIN_ACH:.1f}")
c3.metric("Power Draw", f"{(num_fans * fan_wattage)/1000:.2f} kW")

if calc_ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Non-Compliant: Below SS 553 standard ({SS_553_MIN_ACH} ACH). Add more fans.")
else:
    st.success("✅ Compliant with ventilation standards.")

# Visualization
X, Y, V = simulate_airflow(width, length, num_fans, fan_choice)

fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, width), y=np.linspace(0, length, length),
    colorscale='IceFire', colorbar=dict(title="Velocity (m/s)")
))

fig.update_layout(title="Predicted Air Velocity Distribution", xaxis_title="Width (m)", yaxis_title="Length (m)")
st.plotly_chart(fig, use_container_width=True)
