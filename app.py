import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- STANDARDS (Singapore SS 553) ---
SS_553_MIN_ACH = 20
FAN_TYPES = {
    "HVLS (High Volume Low Speed)": {"wattage": 1500, "cfm": 35000, "radius": 4.5},
    "Standard Ceiling Fan": {"wattage": 85, "cfm": 11000, "radius": 1.2},
    "Industrial Wall Fan": {"wattage": 65, "cfm": 6000, "radius": 0.8}
}

st.set_page_config(page_title="SG Hawker Airflow Pro", layout="wide")

# --- UI SIDEBAR ---
st.sidebar.header("📐 Site Dimensions")
shape_type = st.sidebar.radio("Layout Shape", ["Regular (Rectangular)", "Odd (L-Shape)"])
width = st.sidebar.number_input("Bounding Width (m)", 10, 100, 30)
length = st.sidebar.number_input("Bounding Length (m)", 10, 100, 40)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

st.sidebar.header("🌀 Fan Settings")
fan_choice = st.sidebar.selectbox("Fan Model", list(FAN_TYPES.keys()))
num_fans = st.sidebar.slider("Number of Fans", 1, 30, 6)

# --- DONATION SECTION ---
st.sidebar.markdown("---")
st.sidebar.header("💖 Support This App")
st.sidebar.markdown(
    "If you find this tool useful and would like to support its development, "
    "consider buying me a coffee!"
)
# Replace the URL below with your actual PayPal.Me link or donation button URL.
paypal_url = "https://paypal.me/YOUR_PAYPAL_USERNAME"  # <-- CHANGE THIS
st.sidebar.markdown(
    f"<a href='{paypal_url}' target='_blank'>"
    "<img src='https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif' "
    "alt='Donate via PayPal' style='width: 150px;'></a>",
    unsafe_allow_html=True
)
st.sidebar.markdown("Any amount is greatly appreciated! 🙏")

# --- SIMULATION ENGINE ---
def run_simulation(w, l, n, f_type, shape):
    # Create high-res grid
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)

    # 1. Apply Shape Mask (Physical Boundary)
    mask = np.ones_like(X)
    if shape == "Odd (L-Shape)":
        # Remove top-right 40% of the bounding box
        mask[(X > w*0.6) & (Y > l*0.6)] = np.nan

    net_area = np.nansum(mask)  # Each cell is 1m²

    # 2. Place Fans (Grid Logic)
    rows = int(np.sqrt(n))
    cols = (n // rows) + (1 if n % rows != 0 else 0)
    r_eff = FAN_TYPES[f_type]["radius"]
    strength = FAN_TYPES[f_type]["cfm"] / 10000

    for i in range(n):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)

        # Only place fan if it's within the 'building'
        if shape == "Odd (L-Shape)" and (fx > w*0.6 and fy > l*0.6):
            continue  # Fan is in the 'cutout' area, skip placement

        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        V += strength * np.exp(-dist / (r_eff * 1.5))

    # Apply mask to velocity field
    V = V * mask
    return X, Y, V, net_area

# --- DASHBOARD & ANALYTICS ---
X, Y, V, actual_area = run_simulation(width, length, num_fans, fan_choice, shape_type)

vol_ft3 = (actual_area * height) * 35.3147
calc_ach = (num_fans * FAN_TYPES[fan_choice]["cfm"] * 60) / vol_ft3

st.title(f"🇸🇬 Airflow Simulation: {shape_type} Layout")
st.markdown(f"**Compliance Check:** SS 553 Target = `{SS_553_MIN_ACH} ACH` for Eating Houses.")

c1, c2, c3 = st.columns(3)
c1.metric("Effective Floor Area", f"{actual_area:.1f} m²")
c2.metric("Calculated ACH", f"{calc_ach:.1f}", delta=f"{calc_ach - SS_553_MIN_ACH:.1f}")
c3.metric("Fan Power Usage", f"{(num_fans * FAN_TYPES[fan_choice]['wattage'])/1000:.2f} kW")

if calc_ach < SS_553_MIN_ACH:
    st.error("⚠️ Failed Compliance: Insufficient air changes for this volume.")
else:
    st.success("✅ Compliance Met: Adequate ventilation for current occupant load.")

# --- VISUALIZATION ---
fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, width), y=np.linspace(0, length, length),
    colorscale='Viridis', zmin=0, zmax=5,
    colorbar=dict(title="Velocity (m/s)")
))

fig.update_layout(
    title=f"Air Velocity Profile: {shape_type}",
    xaxis_title="Width (m)", yaxis_title="Length (m)", height=600,
    plot_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, use_container_width=True)

st.info("**Observation:** Notice how 'L-Shape' corners far from fan centers result in dark blue stagnant zones, even if total ACH is high.")
