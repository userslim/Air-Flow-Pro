import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- STANDARDS & SPECS (Singapore SS 553) ---
SS_553_TARGET_ACH = 20  
ELECTRICITY_RATE = 0.32  # Estimated S$/kWh for 2026

# Fan specifications based on typical Singapore industrial models
FAN_SPECS = {
    "HVLS (High Volume Low Speed)": {"wattage": 1500, "cfm": 35000, "radius": 4.5, "desc": "Ideal for open-plan centers."},
    "Industrial Ceiling Fan": {"wattage": 85, "cfm": 12000, "radius": 1.5, "desc": "Standard for high-density seating."},
    "Wall Mount Fan": {"wattage": 65, "cfm": 6500, "radius": 0.8, "desc": "Targeted spot cooling for stalls."}
}

st.set_page_config(page_title="SG Hawker Airflow Simulator", layout="wide")

# --- UI SIDEBAR ---
st.sidebar.header("📍 Building Layout")
app_type = st.sidebar.selectbox("Application", ["Hawker Center", "Wet Market", "Industrial Canteen"])
width = st.sidebar.number_input("Width (m)", 5.0, 100.0, 30.0)
length = st.sidebar.number_input("Length (m)", 5.0, 100.0, 40.0)
height = st.sidebar.number_input("Ceiling Height (m)", 3.0, 10.0, 5.0)

st.sidebar.header("🌀 Fan Selection")
fan_choice = st.sidebar.selectbox("Fan Type", list(FAN_SPECS.keys()))
num_fans = st.sidebar.slider("Number of Fans", 1, 40, 6)
st.sidebar.info(FAN_SPECS[fan_choice]["desc"])

# --- CALCULATIONS ---
volume_m3 = width * length * height
volume_ft3 = volume_m3 * 35.3147  # Convert to cubic feet
total_cfm = num_fans * FAN_SPECS[fan_choice]["cfm"]
ach_calculated = (total_cfm * 60) / volume_ft3
total_kw = (num_fans * FAN_SPECS[fan_choice]["wattage"]) / 1000
est_monthly_cost = total_kw * 12 * 30 * ELECTRICITY_RATE # 12h daily operation

# --- MAIN DASHBOARD ---
st.title(f"🇸🇬 Airflow Simulation: {app_type}")
st.markdown(f"**Compliance Check:** Target Air Changes per Hour (SS 553): `{SS_553_TARGET_ACH} ACH`")

c1, c2, c3 = st.columns(3)
c1.metric("Total Airflow", f"{total_cfm:,} CFM")
c2.metric("Calculated ACH", f"{ach_calculated:.1f}", delta=f"{ach_calculated - SS_553_TARGET_ACH:.1f}")
c3.metric("Est. Monthly Cost", f"S${est_monthly_cost:.2f}")

if ach_calculated < SS_553_TARGET_ACH:
    st.error(f"⚠️ Warning: Below SS 553 requirement for {app_type}. Increase fan count or use HVLS fans.")
else:
    st.success("✅ Compliance: Meets ventilation requirements.")

# --- PHYSICS SIMULATION (Simplified Vector Grid) ---
def generate_sim_data(w, l, n, f_type):
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)
    
    # Place fans in a grid pattern
    rows = int(np.sqrt(n))
    cols = (n // rows) + (1 if n % rows != 0 else 0)
    
    r_val = FAN_SPECS[f_type]["radius"]
    strength = FAN_SPECS[f_type]["cfm"] / 8000
    
    for i in range(n):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        # Decay model: velocity decreases with distance from fan center
        V += strength * np.exp(-dist / (r_val * 1.5))
    
    return X, Y, V

# --- VISUALIZATION ---
X, Y, V = generate_sim_data(width, length, num_fans, fan_choice)

fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, width), y=np.linspace(0, length, length),
    colorscale='IceFire', zmin=0, zmax=5,
    colorbar=dict(title="Velocity (m/s)")
))

fig.update_layout(
    title="Predicted Air Velocity Distribution (at Occupant Level)",
    xaxis_title="Width (meters)", yaxis_title="Length (meters)",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

st.info("**Legend:** Red zones indicate direct airflow (>1.5 m/s), Blue zones indicate stagnant air potential.")
