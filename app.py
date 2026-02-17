import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION & STANDARDS ---
SS_553_MIN_ACH = 20  # Minimum Air Changes per Hour for Hawker Centers
FAN_TYPES = {
    "HVLS (Low Speed High Volume)": {"wattage": 1500, "cfm": 30000, "radius": 3.5}, # 7m diameter
    "Standard Ceiling Fan": {"wattage": 80, "cfm": 10000, "radius": 0.75},
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
num_fans = st.sidebar.slider("Number of Fans", 1, 20, 4)
fan_wattage = st.sidebar.number_input("Fan Wattage (W)", 1, 5000, FAN_TYPES[fan_choice]["wattage"])

# --- PHYSICS ENGINE (Simplified 2D Airflow) ---
def simulate_airflow(w, l, n_fans, f_type):
    # Create grid (1 point per meter)
    x = np.linspace(0, w, w)
    y = np.linspace(0, l, l)
    X, Y = np.meshgrid(x, y)
    
    # Initialize velocity field
    u = np.zeros_like(X)
    v = np.zeros_like(X)
    
    # Place fans in a grid pattern
    rows = int(np.sqrt(n_fans))
    cols = (n_fans // rows) + (1 if n_fans % rows != 0 else 0)
    
    fan_r = FAN_TYPES[f_type]["radius"]
    strength = FAN_TYPES[f_type]["cfm"] / 1000 # Normalized strength
    
    for i in range(n_fans):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        
        # Distance from fan
        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        
        # Airflow falls off with distance (Gaussian-like spread)
        effect = strength * np.exp(-dist / (fan_r * 2))
        u += (X - fx) / (dist + 0.1) * effect
        v += (Y - fy) / (dist + 0.1) * effect

    velocity = np.sqrt(u**2 + v**2)
    return X, Y, velocity

# --- MAIN DASHBOARD ---
st.title("🇸🇬 Indoor Airflow Simulation: Hawker Center & Markets")
st.markdown(f"**Compliance Check:** Target Air Changes per Hour (SS 553): `{SS_553_MIN_ACH} ACH`")

# Calculations
total_cfm = num_fans * FAN_TYPES[fan_choice]["cfm"]
volume_ft3 = (width * length * height) * 35.3147 # m3 to ft3
calc_ach = (total_cfm * 60) / volume_ft3

col1, col2, col3 = st.columns(3)
col1.metric("Total Airflow", f"{total_cfm:,} CFM")
col2.metric("Calculated ACH", f"{calc_ach:.1f}", delta=f"{calc_ach - SS_553_MIN_ACH:.1f} vs Std")
col3.metric("Total Power", f"{(num_fans * fan_wattage)/1000:.2f} kW")

if calc_ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Warning: Below SS 553 requirement of {SS_553_MIN_ACH} ACH for markets/food centers.")
else:
    st.success("✅ Meets ventilation requirements.")

# Simulation Visualization
X, Y, V = simulate_airflow(width, length, num_fans, fan_choice)

fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, width), y=np.linspace(0, length, length),
    colorscale='Viridis',
    colorbar=dict(title="Velocity (m/s approx)")
))

fig.update_layout(
    title=f"Air Velocity Distribution (Occupant Level)",
    xaxis_title="Width (meters)",
    yaxis_title="Length (meters)",
    width=800, height=600
)

st.plotly_chart(fig, use_container_width=True)

st.info("""
**Legend:** * **Purple/Blue:** Dead zones (Low airflow).
* **Green/Yellow:** Optimal circulation areas.
* **Note:** This simulation assumes an open-plan layout typical of NEA hawker centers.
""")