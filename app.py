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
shape_type = st.sidebar.radio("Layout Shape", ["Regular (Rectangular)", "Custom L-Shape"])

# Bounding Box
width = st.sidebar.number_input("Total Bounding Width (m)", 10, 100, 30)
length = st.sidebar.number_input("Total Bounding Length (m)", 10, 100, 40)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

# Custom Perimeter Logic
cutout_w = 0
cutout_l = 0
if shape_type == "Custom L-Shape":
    st.sidebar.subheader("✂️ Cutout Settings")
    st.sidebar.info("Adjust sliders to define the missing corner of the L-shape.")
    cutout_w = st.sidebar.slider("Cutout Width (m)", 0, int(width-2), 12)
    cutout_l = st.sidebar.slider("Cutout Length (m)", 0, int(length-2), 16)

st.sidebar.header("🌀 Fan Settings")
fan_choice = st.sidebar.selectbox("Fan Model", list(FAN_TYPES.keys()))
num_fans_requested = st.sidebar.slider("Number of Fans", 1, 50, 8)

# --- DONATION SECTION ---
st.sidebar.markdown("---")
st.sidebar.header("☕ Support Development")
st.sidebar.write("If this tool helps your project, consider supporting its maintenance!")

# ACTION REQUIRED: Replace 'YOUR_PAYPAL_USERNAME' with your actual username
# Example: "https://paypal.me/johndoe"
my_paypal_username = "YOUR_PAYPAL_USERNAME" 
paypal_link = f"https://www.paypal.com/ncp/payment/CP7XWNDW8NALY"

st.sidebar.markdown(
    f"""
    <a href="{paypal_link}" target="_blank">
        <div style="
            background-color: #0070ba;
            color: white;
            padding: 10px;
            text-align: center;
            border-radius: 5px;
            font-weight: bold;
            text-decoration: none;
            display: block;
        ">
            Donate via PayPal 💳
        </div>
    </a>
    """,
    unsafe_allow_html=True
)
st.sidebar.caption("Thank you for your generosity! 🙏")

# --- SIMULATION ENGINE ---
def run_simulation(w, l, n, f_type, shape, cw, cl):
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)

    mask = np.ones_like(X)
    if shape == "Custom L-Shape":
        mask[(X > (w - cw)) & (Y > (l - cl))] = np.nan

    net_area = np.nansum(mask)

    rows = int(np.sqrt(n))
    cols = (n // rows) + (1 if n % rows != 0 else 0)
    r_eff = FAN_TYPES[f_type]["radius"]
    strength = FAN_TYPES[f_type]["cfm"] / 10000

    placed_fans = 0
    for i in range(n):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        is_in_cutout = (shape == "Custom L-Shape") and (fx > (w - cw) and fy > (l - cl))
        
        if not is_in_cutout:
            placed_fans += 1
            dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
            V += strength * np.exp(-dist / (r_eff * 1.5))

    V = V * mask
    return X, Y, V, net_area, placed_fans

# --- DASHBOARD & ANALYTICS ---
X, Y, V, actual_area, actual_fans = run_simulation(
    width, length, num_fans_requested, fan_choice, shape_type, cutout_w, cutout_l
)

vol_ft3 = (actual_area * height) * 35.3147
calc_ach = (actual_fans * FAN_TYPES[fan_choice]["cfm"] * 60) / vol_ft3

st.title(f"🇸🇬 Airflow Simulation: {shape_type}")
st.markdown(f"**Compliance Check:** SS 553 Target = `{SS_553_MIN_ACH} ACH` for Eating Houses.")

c1, c2, c3 = st.columns(3)
c1.metric("Effective Floor Area", f"{actual_area:.1f} m²")
c2.metric("Calculated ACH", f"{calc_ach:.1f}", delta=f"{calc_ach - SS_553_MIN_ACH:.1f}")
c3.metric("Fans Active", f"{actual_fans} of {num_fans_requested}")

if calc_ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Failed Compliance: Insufficient air changes ({calc_ach:.1f} ACH).")
else:
    st.success("✅ Compliance Met: Adequate ventilation for current occupant load.")

# --- VISUALIZATION ---
fig = go.Figure(data=go.Heatmap(
    z=V, 
    x=np.linspace(0, width, int(width)), 
    y=np.linspace(0, length, int(length)),
    colorscale='Viridis', zmin=0, zmax=5,
    colorbar=dict(title="Velocity (m/s)")
))

fig.update_layout(
    title=f"Air Velocity Profile (Active Fans: {actual_fans})",
    xaxis_title="Width (m)", yaxis_title="Length (m)", height=600
)

st.plotly_chart(fig, use_container_width=True)

