import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# --- STANDARDS & LIMITS ---
SS_553_MIN_ACH = 20
SP_APPROVED_LOAD_KVA = 1120          # total building load limit
DEFAULT_OTHER_LOAD_KW = 1000          # typical other loads (lighting, outlets, etc.) – user adjustable

# --- FAN DATABASE (from RFI document) ---
FAN_DATABASE = {
    "8-Blade Powerfoil 8 (3.6m)": {
        "diameter": 3.6,
        "blades": 8,
        "weight_kg": 91,
        "power_w": 1100,
        "cfm": 287000,
        "max_rpm": 135,
        "isolator": "32A Single Phase",
        "manufacturer": "Big Ass Fans"
    },
    "8-Blade Powerfoil 8 (4.3m)": {
        "diameter": 4.3,
        "blades": 8,
        "weight_kg": 95,
        "power_w": 1500,
        "cfm": 360500,
        "max_rpm": 109,
        "isolator": "32A Single Phase",
        "manufacturer": "Big Ass Fans"
    },
    "6-Blade HORIZON (1.8m)": {
        "diameter": 1.8,
        "blades": 6,
        "weight_kg": 35,
        "power_w": 500,
        "cfm": 175000,
        "max_rpm": 90,
        "isolator": "20A Single Phase",
        "manufacturer": "Spacefans"
    },
    "6-Blade HORIZON (3.6m)": {
        "diameter": 3.6,
        "blades": 6,
        "weight_kg": 53,
        "power_w": 500,
        "cfm": 287000,
        "max_rpm": 67,
        "isolator": "20A Single Phase",
        "manufacturer": "Spacefans"
    },
    "6-Blade HORIZON (4.3m)": {
        "diameter": 4.3,
        "blades": 6,
        "weight_kg": 60,
        "power_w": 500,
        "cfm": 360500,
        "max_rpm": 58,
        "isolator": "20A Single Phase",
        "manufacturer": "Spacefans"
    }
}

# Pre‑configured project scenarios from the document
PROJECT_SCENARIOS = {
    "Original Design (8-Blade, 3.6m + 4.3m)": {
        "fans": [
            {"model": "8-Blade Powerfoil 8 (3.6m)", "quantity": 14},
            {"model": "8-Blade Powerfoil 8 (4.3m)", "quantity": 14}
        ]
    },
    "Alternative 1 (6-Blade HORIZON 1.8m + 3.6m)": {
        "fans": [
            {"model": "6-Blade HORIZON (1.8m)", "quantity": 41},
            {"model": "6-Blade HORIZON (3.6m)", "quantity": 14}
        ]
    },
    "Alternative 2 (6-Blade HORIZON 4.3m only)": {
        "fans": [
            {"model": "6-Blade HORIZON (4.3m)", "quantity": 14}
        ]
    }
}

st.set_page_config(page_title="SG Hawker Airflow Pro - Optimised", layout="wide")

# --- SIDEBAR ---
st.sidebar.header("🏢 Project: Tanglin Halt Hawker Centre")
st.sidebar.info("Based on RFI Submission NCB-THC2-RFA-DT-ME-ELE-001B")

# Non‑fan load input
st.sidebar.header("⚡ Power Budget")
other_load = st.sidebar.number_input(
    "Estimated non‑fan load (kW)",
    min_value=0.0,
    max_value=float(SP_APPROVED_LOAD_KVA),
    value=float(DEFAULT_OTHER_LOAD_KW),
    step=10.0,
    help="Total load of lighting, outlets, equipment, etc. Must be ≤ 1120 kVA."
)
max_fan_power_kw = SP_APPROVED_LOAD_KVA - other_load
if max_fan_power_kw < 0:
    st.sidebar.error("Non‑fan load exceeds total limit! Adjust other load.")
    max_fan_power_kw = 0

st.sidebar.metric("Available for Fans", f"{max_fan_power_kw:.1f} kW")

# Fan selection (scenario or custom)
use_scenario = st.sidebar.checkbox("Use Pre‑configured Project Scenarios", value=True)

if use_scenario:
    scenario = st.sidebar.selectbox("Select Configuration", list(PROJECT_SCENARIOS.keys()))
    fan_configs = PROJECT_SCENARIOS[scenario]["fans"]
    
    st.sidebar.subheader("📋 Fan Configuration")
    for config in fan_configs:
        st.sidebar.text(f"{config['model']}: {config['quantity']} nos")
    
    total_fans = sum(config["quantity"] for config in fan_configs)
    total_power = sum(FAN_DATABASE[config["model"]]["power_w"] * config["quantity"] / 1000 
                     for config in fan_configs)
    st.sidebar.metric("Total Fans", f"{total_fans} nos")
    st.sidebar.metric("Total Fan Power", f"{total_power:.1f} kW")
    
else:
    st.sidebar.header("🌀 Custom Fan Selection")
    fan_choice = st.sidebar.selectbox("Fan Model", list(FAN_DATABASE.keys()))
    num_fans_requested = st.sidebar.slider("Number of Fans", 1, 50, 10)
    fan_configs = [{"model": fan_choice, "quantity": num_fans_requested}]

st.sidebar.header("📐 Site Dimensions")
width = st.sidebar.number_input("Canvas Width (m)", 10, 100, 40)
length = st.sidebar.number_input("Canvas Length (m)", 10, 100, 40)
height = st.sidebar.number_input("Ceiling Height (m)", 3, 10, 5)

st.sidebar.header("📍 Layout Shape")
shape_type = st.sidebar.radio("Layout Shape", ["Regular (Rectangular)", "Custom L-Shape", "Composite"])

params = {}
if shape_type == "Custom L-Shape":
    params['cw'] = st.sidebar.slider("Cutout Width (m)", 0, int(width-2), 12)
    params['cl'] = st.sidebar.slider("Cutout Length (m)", 0, int(length-2), 16)
elif shape_type == "Composite":
    st.sidebar.subheader("Composite Components")
    params['rect_w'] = st.sidebar.slider("Main Rectangle Width (m)", 5, int(width), 20)
    params['rect_l'] = st.sidebar.slider("Main Rectangle Length (m)", 5, int(length), 30)
    params['tri_base'] = st.sidebar.slider("Triangle Base (m)", 0, int(width), 15)
    params['tri_height'] = st.sidebar.slider("Triangle Height (m)", 0, int(length), 10)
    params['circ_r'] = st.sidebar.slider("Circle Radius (m)", 0, int(min(width, length)/2), 8)

st.sidebar.header("📷 Actual Area Image")
uploaded_image = st.sidebar.file_uploader("Upload floor plan photo", type=['png', 'jpg', 'jpeg'])

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

# --- SIMULATION ENGINE (unchanged) ---
def run_simulation(w, l, h, fan_configs, shape, p):
    x = np.linspace(0, w, int(w))
    y = np.linspace(0, l, int(l))
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)

    mask = np.full(X.shape, np.nan)
    if shape == "Regular (Rectangular)":
        mask[:, :] = 1
    elif shape == "Custom L-Shape":
        mask_logic = ~((X > (w - p['cw'])) & (Y > (l - p['cl'])))
        mask[mask_logic] = 1
    elif shape == "Composite":
        rect = (X <= p['rect_w']) & (Y <= p['rect_l'])
        tri = (X <= p['tri_base']) & (Y > p['rect_l']) & (Y <= p['rect_l'] + p['tri_height'])
        dist_from_center = np.sqrt((X - p['rect_w'])**2 + (Y - (p['rect_l']/2))**2)
        circ = dist_from_center <= p['circ_r']
        mask_logic = rect | tri | circ
        mask[mask_logic] = 1

    net_area = np.nansum(mask)
    volume_m3 = net_area * h
    volume_ft3 = volume_m3 * 35.3147

    placed_fans = []
    total_airflow_cfm = 0
    total_power_w = 0

    for config in fan_configs:
        model = config["model"]
        quantity = config["quantity"]
        fan_data = FAN_DATABASE[model]

        rows = int(np.sqrt(quantity))
        cols = (quantity // rows) + (1 if quantity % rows != 0 else 0)

        r_eff = fan_data["diameter"] / 2
        strength = fan_data["cfm"] / 20000

        placed = 0
        for i in range(quantity):
            fx = (i % cols + 0.5) * (w / cols)
            fy = (i // cols + 0.5) * (l / rows)

            ix, iy = int(min(fx, w-1)), int(min(fy, l-1))
            if not np.isnan(mask[iy, ix]):
                placed += 1
                dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
                V += strength * np.exp(-dist / (r_eff * 1.5))
                placed_fans.append({"model": model, "x": fx, "y": fy})

        total_airflow_cfm += fan_data["cfm"] * placed
        total_power_w += fan_data["power_w"] * placed

    ach = (total_airflow_cfm * 60) / volume_ft3 if volume_ft3 > 0 else 0
    return X, Y, V * mask, net_area, volume_m3, placed_fans, total_airflow_cfm, total_power_w, ach

# --- EXECUTION ---
X, Y, V, actual_area, volume, placed_fans, total_cfm, total_power, ach = run_simulation(
    width, length, height, fan_configs, shape_type, params
)

# --- DISPLAY RESULTS ---
st.title(f"🇸🇬 Airflow Simulation: Tanglin Halt Hawker Centre")
st.info(f"Compliance: SS 553 requires ≥ {SS_553_MIN_ACH} ACH. Total building load limit: {SP_APPROVED_LOAD_KVA} kVA (including fans).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Effective Floor Area", f"{actual_area:.1f} m²")
c2.metric("Volume", f"{volume:.1f} m³")
c3.metric("Calculated ACH", f"{ach:.1f}", delta=f"{ach - SS_553_MIN_ACH:.1f}")
c4.metric("Total Fan Power", f"{total_power/1000:.2f} kW")

if ach < SS_553_MIN_ACH:
    st.error(f"⚠️ Airflow non‑compliant ({ach:.1f} ACH).")
else:
    st.success("✅ Airflow meets SS 553.")

# Power compliance
if total_power/1000 > max_fan_power_kw:
    st.error(f"⚠️ Fan power ({total_power/1000:.2f} kW) exceeds available budget ({max_fan_power_kw:.2f} kW). Reduce fans or increase other load estimate.")
else:
    st.success(f"✅ Fan power within budget (available: {max_fan_power_kw:.2f} kW).")

# --- OPTIMISATION RECOMMENDATION ---
st.subheader("💡 Optimisation Recommendation")
st.markdown("Find a fan configuration that meets ≥20 ACH and stays within the power budget.")

if st.button("Run Optimisation (single model)"):
    best_model = None
    best_qty = 0
    best_ach = 0
    results = []
    volume_ft3 = volume * 35.3147  # already computed

    for model, data in FAN_DATABASE.items():
        # Maximum quantity based on power budget
        max_qty_by_power = int(max_fan_power_kw * 1000 // data["power_w"])
        if max_qty_by_power == 0:
            continue

        # Find the smallest quantity that meets ACH
        # ACH = (qty * data["cfm"] * 60) / volume_ft3
        required_qty_ach = max(1, int(np.ceil(SS_553_MIN_ACH * volume_ft3 / (data["cfm"] * 60))))
        qty = min(required_qty_ach, max_qty_by_power)

        if qty == 0:
            continue

        # Recalculate ACH with this qty
        ach_achieved = (qty * data["cfm"] * 60) / volume_ft3
        power_used = qty * data["power_w"] / 1000
        results.append({
            "Model": model,
            "Quantity": qty,
            "ACH": round(ach_achieved, 1),
            "Power (kW)": round(power_used, 2),
            "Meets ACH": "✅" if ach_achieved >= SS_553_MIN_ACH else "❌",
            "Within Power": "✅" if power_used <= max_fan_power_kw else "❌"
        })

        if ach_achieved >= SS_553_MIN_ACH and power_used <= max_fan_power_kw:
            if ach_achieved > best_ach:
                best_ach = ach_achieved
                best_model = model
                best_qty = qty

    if results:
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True)

        if best_model:
            st.success(f"**Recommended:** {best_qty} x {best_model} → ACH = {best_ach:.1f}, Power = {best_qty * FAN_DATABASE[best_model]['power_w'] / 1000:.2f} kW")
        else:
            st.warning("No single fan model can meet both ACH and power limits. Consider a combination of models or reduce other loads.")
    else:
        st.error("Insufficient power budget for any fan. Increase power budget or reduce other loads.")

# --- ADDITIONAL INFO (from document) ---
st.subheader("⚡ Power Load Context")
st.markdown(f"""
**SP Approved Total Building Load:** {SP_APPROVED_LOAD_KVA} kVA  
**Non‑fan load (your estimate):** {other_load:.1f} kW  
**Available for fans:** {max_fan_power_kw:.1f} kW  
**Current fan load:** {total_power/1000:.2f} kW  

*Note: Fan load is only part of the total building load. The overall electrical design (including lighting, outlets, etc.) must not exceed {SP_APPROVED_LOAD_KVA} kVA.*
""")

# Reference table from RFI (Page 45)
st.markdown("**Reference from RFI (Page 45):**")
load_data = {
    "Configuration": ["8-Blade Design (with 1.8m)", "6-Blade Design"],
    "Total Fan Power (kW)": [75.9, 34.5],
    "Annual Cost (SGD)": [5007, 1316],
    "Daily Cost (SGD)": [13.72, 3.60]
}
df_load = pd.DataFrame(load_data)
st.dataframe(df_load, use_container_width=True)

# Fan configuration summary
st.subheader("🌀 Fan Configuration Summary")
fan_summary = []
for config in fan_configs:
    model = config["model"]
    qty = config["quantity"]
    fan_data = FAN_DATABASE[model]
    fan_summary.append({
        "Model": model,
        "Diameter": f"{fan_data['diameter']}m",
        "Blades": fan_data['blades'],
        "Quantity": qty,
        "Power per Fan": f"{fan_data['power_w']}W",
        "Total Power": f"{fan_data['power_w'] * qty / 1000:.1f} kW",
        "CFM per Fan": f"{fan_data['cfm']:,}",
        "Total CFM": f"{fan_data['cfm'] * qty:,}"
    })
st.dataframe(pd.DataFrame(fan_summary), use_container_width=True)

# --- VISUALISATION (unchanged) ---
st.subheader("📊 Airflow Visualization")

if uploaded_image is not None:
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Simulated Airflow (After Analysis)", "Uploaded Floor Plan (Before)"),
        specs=[[{"type": "heatmap"}, {"type": "image"}]]
    )
    heatmap = go.Heatmap(
        z=V, x=np.linspace(0, width, int(width)), y=np.linspace(0, length, int(length)),
        colorscale='Viridis', zmin=0, zmax=3, colorbar=dict(title="m/s")
    )
    fig.add_trace(heatmap, row=1, col=1)
    from PIL import Image
    img = Image.open(uploaded_image)
    fig.add_trace(go.Image(z=img), row=1, col=2)
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    fig = go.Figure(data=go.Heatmap(
        z=V, x=np.linspace(0, width, int(width)), y=np.linspace(0, length, int(length)),
        colorscale='Viridis', zmin=0, zmax=3, colorbar=dict(title="m/s")
    ))
    fig.update_layout(title="Airflow Velocity Distribution", height=600)
    st.plotly_chart(fig, use_container_width=True)

# Fan placement overlay
if st.checkbox("Show Fan Placement"):
    fig2 = go.Figure()
    fig2.add_trace(go.Heatmap(
        z=V, x=np.linspace(0, width, int(width)), y=np.linspace(0, length, int(length)),
        colorscale='Viridis', zmin=0, zmax=3, showscale=False, opacity=0.7
    ))
    for fan in placed_fans:
        model = fan["model"]
        color = "red" if "8-Blade" in model else "blue"
        fig2.add_trace(go.Scatter(
            x=[fan["x"]], y=[fan["y"]],
            mode='markers+text',
            marker=dict(size=12, color=color, symbol='circle'),
            text=model.split()[0],
            textposition="top center",
            name=model,
            showlegend=False
        ))
    fig2.update_layout(
        title="Fan Placement Overlay",
        xaxis_title="Width (m)",
        yaxis_title="Length (m)",
        height=600
    )
    st.plotly_chart(fig2, use_container_width=True)

# Recommendations from RFI
st.subheader("📋 Recommendations from RFI")
st.info("""
- The location of HVLS fan shall be reviewed in conjunction with the lighting layout to prevent any throbbing effect.
- Fan and lighting location shall not overlap.
- Location and height to be reviewed and approved with architect.
- 6-blade fans consume less power than 8-blade fans.
- SP load upgrading may be required if total building load exceeds 1120 kVA.
""")

# Download report
if st.button("📥 Download Simulation Report"):
    report = f"""TANGLIN HALT HAWKER CENTRE - AIRFLOW SIMULATION REPORT
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

CONFIGURATION:
{chr(10).join([f"- {c['model']}: {c['quantity']} nos" for c in fan_configs])}

RESULTS:
- Floor Area: {actual_area:.1f} m²
- Volume: {volume:.1f} m³
- Total Airflow: {total_cfm:,.0f} CFM
- Air Changes per Hour (ACH): {ach:.1f}
- SS 553 Requirement: {SS_553_MIN_ACH} ACH
- Compliance: {'PASS' if ach >= SS_553_MIN_ACH else 'FAIL'}

POWER:
- Non‑fan load (estimate): {other_load:.1f} kW
- Fan Load: {total_power/1000:.2f} kW
- Total Load: {other_load + total_power/1000:.2f} kW  (approx. kVA)
- SP Approved Total Building Load: {SP_APPROVED_LOAD_KVA} kVA
- Compliance: {'PASS' if (other_load + total_power/1000) <= SP_APPROVED_LOAD_KVA else 'FAIL'}

RECOMMENDATIONS:
- Review fan locations with lighting layout
- Avoid overlapping fan and light positions
- Obtain architect approval for final positions
- Ensure total building load ≤ {SP_APPROVED_LOAD_KVA} kVA
"""
    st.download_button(
        label="Download Text Report",
        data=report,
        file_name=f"airflow_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )
