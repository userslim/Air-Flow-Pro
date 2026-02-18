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
shape_type = st.sidebar.radio("Layout Shape", ["Regular (Rectangular)", "Custom L-Shape", "Composite (Rect+Tri+Circ)"])

# Bounding Box (The Canvas)
width = st.sidebar.number_input("Canvas Width (m)", 10, 100, 40)
length = st.sidebar.number_input("Canvas Length (m)", 10, 100, 40)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

# --- SHAPE LOGIC ---
params = {}
if shape_type == "Custom L-Shape":
    params['cw'] = st.sidebar.slider("Cutout Width (m)", 0, int(width-2), 12)
    params['cl'] = st.sidebar.slider("Cutout Length (m)", 0, int(length-2), 16)

elif shape_type == "Composite (Rect+Tri+Circ)":
    st.sidebar.subheader("💎 Composite Components")
    params['rect_w'] = st.sidebar.slider("Main Rectangle Width (m)", 5, int(width), 20)
    params['rect_l'] = st.sidebar.slider("Main Rectangle Length (m)", 5, int(length), 30)
    params['tri_base'] = st.sidebar.slider("Triangle Base (m)", 0, int(width), 15)
    params['tri_height'] = st.sidebar.slider("Triangle Height (m)", 0, int(length), 10)
    params['circ_r'] = st.sidebar.slider("Circle Radius (m)", 0, int(min(width, length)/2), 8)

st.sidebar.header("🌀 Fan Settings")
fan_choice = st.sidebar.selectbox("Fan Model", list(FAN_TYPES.keys()))
num_fans_requested = st.sidebar.slider("Number of Fans", 1, 50, 10)

# --- DONATION SECTION ---
st.sidebar.markdown("---")
st.sidebar.header("☕ Support Development")
paypal_link = "https://www.paypal.com/ncp/payment/CP7XWNDW8NALY"

st.sidebar.markdown(
    f"""
    <a href="{paypal_link}" target="_blank">
        <div style="background-color: #0070ba; color: white; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none;">
            Donate via PayPal 💳
        </div>
    </a>
    """, unsafe_allow_html=True
)

# --- SIMULATION ENGINE ---
def run_simulation(w, l, n, f_type, shape, p):
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)

    # 1. Generate Mask
    mask = np.full(X.shape, np.nan)
    
    if shape == "Regular (Rectangular)":
        mask[:, :] = 1
    elif shape == "Custom L-Shape":
        mask_logic = ~((X > (w - p['cw'])) & (Y > (l - p['cl'])))
        mask[mask_logic] = 1
    elif shape == "Composite (Rect+Tri+Circ)":
        # Main Rectangle (Center bottom)
        rect = (X <= p['rect_w']) & (Y <= p['rect_l'])
        # Triangle (Top of rectangle)
        tri = (X <= p['tri_base']) & (Y > p['rect_l']) & (Y <= p['rect_l'] + p['tri_height'])
        # Circle (Right of rectangle)
        dist_from_center = np.sqrt((X - p['rect_w'])**2 + (Y - (p['rect_l']/2))**2)
        circ = dist_from_center <= p['circ_r']
        
        mask_logic = rect | tri | circ
        mask[mask_logic] = 1

    net_area = np.nansum(mask)

    # 2. Fan Placement & Velocity
    rows = int(np.sqrt(n))
    cols = (n // rows) + (1 if n % rows != 0 else 0)
    r_eff = FAN_TYPES[f_type]["radius"]
    strength = FAN_TYPES[f_type]["cfm"] / 10000

    placed_fans = 0
    for i in range(n):
        fx = (i % cols + 0.5) * (w / cols)
        fy = (i // cols + 0.5) * (l / rows)
        
        # Check if fan is inside the mask
        ix, iy = int(min(fx, w-1)), int(min(fy, l-1))
        if not np.isnan(mask[iy, ix]):
            placed_fans += 1
            dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
            V += strength * np.exp(-dist / (r_eff * 1.5))

    return X, Y, V * mask, net_area, placed_fans

# --- EXECUTION ---
X, Y, V, actual_area, actual_fans = run_simulation(width, length, num_fans_requested, fan_choice, shape_type, params)

vol_ft3 = (actual_area * height) * 35.3147
calc_ach = (actual_fans * FAN_TYPES[fan_choice]["cfm"] * 60) / vol_ft3

st.title(f"🇸🇬 Airflow Simulation: {shape_type}")
st.info(f"Compliance Check (SS 553): {SS_553_MIN_ACH} ACH Required.")

c1, c2, c3 = st.columns(3)
c1.metric("Effective Floor Area", f"{actual_area:.1f} m²")
c2.metric("Calculated ACH", f"{calc_ach:.1f}", delta=f"{calc_ach - SS_553_MIN_ACH:.1f}")
c3.metric("Fans in Building", f"{actual_fans}")

if calc_ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Non-Compliant: Need more airflow ({calc_ach:.1f} ACH).")
else:
    st.success("✅ Standards Met.")

fig = go.Figure(data=go.Heatmap(
    z=V, x=np.linspace(0, width, int(width)), y=np.linspace(0, length, int(length)),
    colorscale='Viridis', zmin=0, zmax=5, colorbar=dict(title="m/s")
))
fig.update_layout(title="Velocity Distribution Heatmap", height=600)
st.plotly_chart(fig, use_container_width=True)
