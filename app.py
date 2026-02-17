import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math  # Added for mathematical operations

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
c2.metric("Calculated ACH", f"{ach_calculated:.1f}", delta=f"{ach_calculated - SS_553_TARGET_ACH:.1f} ACH")
c3.metric("Est. Monthly Cost", f"S${est_monthly_cost:.2f}")

if ach_calculated < SS_553_TARGET_ACH:
    st.error(f"⚠️ Warning: Below SS 553 requirement for {app_type}. Increase fan count or use HVLS fans.")
else:
    st.success("✅ Compliance: Meets ventilation requirements.")

# --- PHYSICS SIMULATION (Simplified Vector Grid) ---
def generate_sim_data(w, l, n, f_type):
    # FIX 1: Ensure grid resolution is reasonable (min 20, max 100 points)
    # Convert to integers for grid size
    grid_x = max(20, min(100, int(w)))  # Cap at reasonable resolution
    grid_y = max(20, min(100, int(l)))
    
    x = np.linspace(0, w, grid_x)
    y = np.linspace(0, l, grid_y)
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)
    
    # Place fans in a grid pattern
    rows = int(np.sqrt(n))
    cols = int(np.ceil(n / rows)) if rows > 0 else 1  # FIX 2: Handle division by zero
    
    r_val = FAN_SPECS[f_type]["radius"]
    strength = FAN_SPECS[f_type]["cfm"] / 8000
    
    for i in range(n):
        # FIX 3: Avoid division by zero for rows/cols
        if cols > 0:
            fx = (i % cols + 0.5) * (w / max(cols, 1))
        else:
            fx = w / 2
            
        if rows > 0:
            fy = (i // cols + 0.5) * (l / max(rows, 1)) if cols > 0 else l / 2
        else:
            fy = l / 2
        
        dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
        # Decay model: velocity decreases with distance from fan center
        V += strength * np.exp(-dist / (r_val * 1.5))
    
    return X, Y, V

# --- VISUALIZATION ---
X, Y, V = generate_sim_data(width, length, num_fans, fan_choice)

# FIX 4: Create proper grid for heatmap
fig = go.Figure(data=go.Heatmap(
    z=V, 
    x=np.linspace(0, width, V.shape[1]),  # Use actual shape from generated data
    y=np.linspace(0, length, V.shape[0]),
    colorscale='Jet',  # Changed from IceFire to Jet for better visibility
    zmin=0, 
    zmax=np.max(V) if np.max(V) > 0 else 5,  # FIX 5: Dynamic zmax
    colorbar=dict(title="Velocity (m/s)")
))

# FIX 6: Add fan positions as markers for better visualization
fan_positions_x = []
fan_positions_y = []

rows = int(np.sqrt(num_fans))
cols = int(np.ceil(num_fans / rows)) if rows > 0 else 1

for i in range(num_fans):
    if cols > 0:
        fx = (i % cols + 0.5) * (width / max(cols, 1))
    else:
        fx = width / 2
        
    if rows > 0:
        fy = (i // cols + 0.5) * (length / max(rows, 1)) if cols > 0 else length / 2
    else:
        fy = length / 2
    
    fan_positions_x.append(fx)
    fan_positions_y.append(fy)

# Add fan markers
fig.add_trace(go.Scatter(
    x=fan_positions_x,
    y=fan_positions_y,
    mode='markers',
    marker=dict(
        symbol='circle',
        size=15,
        color='white',
        line=dict(color='black', width=2)
    ),
    name='Fan Positions',
    text=[f'Fan {i+1}' for i in range(num_fans)],
    hoverinfo='text'
))

fig.update_layout(
    title="Predicted Air Velocity Distribution (at Occupant Level)",
    xaxis_title="Width (meters)", 
    yaxis_title="Length (meters)",
    height=600,
    hovermode='closest'
)

st.plotly_chart(fig, use_container_width=True)

# FIX 7: Add additional metrics
col1, col2 = st.columns(2)

with col1:
    # Calculate average velocity
    avg_velocity = np.mean(V)
    st.metric("Average Air Velocity", f"{avg_velocity:.2f} m/s")

with col2:
    # Calculate coverage percentage (areas with velocity > 0.5 m/s)
    coverage = np.sum(V > 0.5) / V.size * 100
    st.metric("Effective Coverage Area", f"{coverage:.1f}%")

# FIX 8: Add recommendations based on results
st.subheader("💡 Recommendations")

if avg_velocity < 0.5:
    st.warning("Low average air velocity detected. Consider adding more fans or using higher CFM models.")
elif avg_velocity < 1.0:
    st.info("Moderate air velocity. Good for general comfort.")
else:
    st.success("Good air velocity. Comfortable environment expected.")

if coverage < 50:
    st.warning(f"Only {coverage:.1f}% of area has effective airflow. Consider repositioning fans for better coverage.")

st.info("**Legend:** White dots indicate fan positions. Warmer colors (red) indicate higher air velocity.")

# FIX 9: Add SS 553 reference note
with st.expander("📚 About SS 553 Standard"):
    st.markdown("""
    **Singapore Standard SS 553: Code of Practice for Air-Conditioning and Mechanical Ventilation in Buildings**
    
    - **Target ACH:** 20 air changes per hour for food establishments
    - **Purpose:** Ensure adequate ventilation for occupant health and comfort
    - **Compliance:** Regular testing and maintenance required
    
    *Note: This simulator provides estimates. Always consult with mechanical engineers for final design.*
    """)

# FIX 10: Add download functionality for report
if st.button("📥 Generate Report Summary"):
    report = f"""
    AIRFLOW SIMULATION REPORT
    ========================
    Date: {st.session_state.get('timestamp', 'N/A')}
    Application: {app_type}
    Dimensions: {width}m x {length}m x {height}m
    Area: {width * length:.1f} m²
    Volume: {volume_m3:.1f} m³
    
    FAN CONFIGURATION
    =================
    Fan Type: {fan_choice}
    Number of Fans: {num_fans}
    Total Airflow: {total_cfm:,} CFM
    
    PERFORMANCE METRICS
    ===================
    Calculated ACH: {ach_calculated:.1f}
    Target ACH (SS 553): {SS_553_TARGET_ACH}
    Status: {'✅ Compliant' if ach_calculated >= SS_553_TARGET_ACH else '❌ Non-compliant'}
    Average Velocity: {avg_velocity:.2f} m/s
    Coverage Area: {coverage:.1f}%
    
    ENERGY COSTS
    ============
    Total Power: {total_kw:.2f} kW
    Estimated Monthly Cost: ${est_monthly_cost:.2f}
    """
    
    st.download_button(
        label="Download Report",
        data=report,
        file_name="airflow_report.txt",
        mime="text/plain"
    )
