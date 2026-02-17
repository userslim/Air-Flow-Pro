import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# --- STANDARDS & SPECS (Singapore SS 553) ---
SS_553_TARGET_ACH = 20  
ELECTRICITY_RATE = 0.32  # Estimated S$/kWh for 2026

# Fan specifications based on typical Singapore industrial models
FAN_SPECS = {
    "HVLS (High Volume Low Speed)": {
        "wattage": 1500, 
        "cfm": 35000, 
        "radius": 4.5, 
        "desc": "Ideal for open-plan centers with high ceilings.",
        "noise_level": "Low",
        "mounting": "Ceiling"
    },
    "Industrial Ceiling Fan": {
        "wattage": 85, 
        "cfm": 12000, 
        "radius": 1.5, 
        "desc": "Standard for high-density seating areas.",
        "noise_level": "Medium",
        "mounting": "Ceiling"
    },
    "Wall Mount Fan": {
        "wattage": 65, 
        "cfm": 6500, 
        "radius": 0.8, 
        "desc": "Targeted spot cooling for stalls and food preparation areas.",
        "noise_level": "Medium-High",
        "mounting": "Wall"
    },
    "Pedestal Fan": {
        "wattage": 75, 
        "cfm": 8000, 
        "radius": 1.0, 
        "desc": "Portable option for flexible positioning.",
        "noise_level": "Medium",
        "mounting": "Floor"
    },
    "Misting Fan": {
        "wattage": 200, 
        "cfm": 10000, 
        "radius": 2.0, 
        "desc": "Provides cooling through evaporation, ideal for outdoor areas.",
        "noise_level": "Medium",
        "mounting": "Floor/Stand"
    }
}

# Application-specific recommendations
APP_RECOMMENDATIONS = {
    "Hawker Center": {
        "primary_fan": "HVLS (High Volume Low Speed)",
        "secondary_fan": "Industrial Ceiling Fan",
        "min_ach": 20,
        "notes": "Combine HVLS for general ventilation with spot fans at busy stalls"
    },
    "Wet Market": {
        "primary_fan": "Industrial Ceiling Fan",
        "secondary_fan": "Wall Mount Fan",
        "min_ach": 15,
        "notes": "Focus on moisture control and targeted airflow at fish/meat stalls"
    },
    "Industrial Canteen": {
        "primary_fan": "HVLS (High Volume Low Speed)",
        "secondary_fan": "Pedestal Fan",
        "min_ach": 18,
        "notes": "HVLS for main dining, portable fans for flexibility during peak hours"
    }
}

st.set_page_config(
    page_title="SG Hawker Airflow Simulator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .compliant {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #28a745;
    }
    .non-compliant {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# --- UI SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/fan--v1.png", width=100)
    st.header("📍 Building Layout")
    
    app_type = st.selectbox(
        "Application", 
        ["Hawker Center", "Wet Market", "Industrial Canteen"],
        help="Select the type of food establishment"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("Width (m)", 5.0, 100.0, 30.0, step=0.5)
    with col2:
        length = st.number_input("Length (m)", 5.0, 100.0, 40.0, step=0.5)
    
    height = st.number_input("Ceiling Height (m)", 3.0, 10.0, 5.0, step=0.5)
    
    st.header("🌀 Fan Selection")
    
    # Show recommended fan types
    rec = APP_RECOMMENDATIONS[app_type]
    st.info(f"💡 Recommended: {rec['primary_fan']} + {rec['secondary_fan']}")
    
    fan_choice = st.selectbox(
        "Fan Type", 
        list(FAN_SPECS.keys()),
        help=FAN_SPECS[list(FAN_SPECS.keys())[0]]["desc"]
    )
    
    num_fans = st.slider("Number of Fans", 1, 40, 6)
    
    # Show fan details
    with st.expander("Fan Details"):
        fan = FAN_SPECS[fan_choice]
        st.write(f"**Description:** {fan['desc']}")
        st.write(f"**Mounting:** {fan['mounting']}")
        st.write(f"**Noise Level:** {fan['noise_level']}")
        st.write(f"**Coverage Radius:** {fan['radius']}m")
    
    # Operating hours
    st.header("⏰ Operating Hours")
    hours_per_day = st.slider("Hours per Day", 4, 24, 12)
    days_per_month = st.slider("Days per Month", 1, 31, 30)

# --- CALCULATIONS ---
area_m2 = width * length
volume_m3 = width * length * height
volume_ft3 = volume_m3 * 35.3147  # Convert to cubic feet
total_cfm = num_fans * FAN_SPECS[fan_choice]["cfm"]
ach_calculated = (total_cfm * 60) / volume_ft3 if volume_ft3 > 0 else 0
total_kw = (num_fans * FAN_SPECS[fan_choice]["wattage"]) / 1000
daily_consumption = total_kw * hours_per_day
monthly_consumption = daily_consumption * days_per_month
est_monthly_cost = monthly_consumption * ELECTRICITY_RATE

# --- MAIN DASHBOARD ---
st.markdown("<h1 class='main-title'>🇸🇬 SG Hawker Airflow Simulator</h1>", unsafe_allow_html=True)

# Top metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Floor Area", f"{area_m2:.0f} m²")
with col2:
    st.metric("Volume", f"{volume_m3:.0f} m³")
with col3:
    st.metric("Total Airflow", f"{total_cfm:,.0f} CFM")
with col4:
    st.metric("Total Power", f"{total_kw:.1f} kW")

# Compliance check
st.markdown(f"**Target Air Changes per Hour (SS 553):** `{SS_553_TARGET_ACH} ACH` for food establishments")

c1, c2 = st.columns(2)
with c1:
    st.metric(
        "Calculated ACH", 
        f"{ach_calculated:.1f} ACH", 
        delta=f"{ach_calculated - SS_553_TARGET_ACH:.1f} ACH",
        delta_color="inverse"
    )

with c2:
    st.metric(
        "Est. Monthly Cost", 
        f"S${est_monthly_cost:.2f}",
        help=f"Based on {hours_per_day}h/day, {days_per_month} days/month"
    )

# Compliance status
if ach_calculated < SS_553_TARGET_ACH:
    st.markdown(f"""
    <div class='non-compliant'>
        ⚠️ <b>Warning:</b> Below SS 553 requirement for {app_type}. 
        Current: {ach_calculated:.1f} ACH | Required: {SS_553_TARGET_ACH} ACH<br>
        <b>Recommendation:</b> Increase fan count by {max(1, int((SS_553_TARGET_ACH - ach_calculated) / ach_calculated * num_fans))} or use HVLS fans.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class='compliant'>
        ✅ <b>Compliance:</b> Meets ventilation requirements for {app_type}.<br>
        Current: {ach_calculated:.1f} ACH | Required: {SS_553_TARGET_ACH} ACH
    </div>
    """, unsafe_allow_html=True)

# --- PHYSICS SIMULATION ---
def generate_sim_data(w, l, h, n, f_type):
    """Generate airflow simulation data"""
    # Create grid with reasonable resolution
    grid_size = 50  # Fixed grid size for performance
    x = np.linspace(0, w, grid_size)
    y = np.linspace(0, l, grid_size)
    X, Y = np.meshgrid(x, y)
    V = np.zeros_like(X)
    
    # Calculate fan positions in a grid pattern
    if n > 0:
        rows = int(np.sqrt(n))
        cols = int(np.ceil(n / rows))
        
        fan_spec = FAN_SPECS[f_type]
        r_val = fan_spec["radius"]
        
        # Base strength factor
        strength = fan_spec["cfm"] / 10000  # Normalized
        
        for i in range(n):
            # Calculate fan position
            if cols > 0:
                fx = (i % cols + 0.5) * (w / cols)
            else:
                fx = w / 2
                
            if rows > 0:
                fy = (i // cols + 0.5) * (l / rows)
            else:
                fy = l / 2
            
            # Calculate distance from fan
            dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
            
            # Airflow model: 
            # - Peak at fan location
            # - Exponential decay with distance
            # - Height factor affects distribution
            height_factor = 1.0 - min(h / 10, 0.5)  # Higher ceilings reduce ground velocity
            
            # Add vertical circulation effect
            vertical_circulation = np.sin(dist / r_val * np.pi/2) * height_factor
            
            # Combine effects
            V += strength * np.exp(-dist / (r_val * 1.5)) * (1 + vertical_circulation * 0.3)
    
    return X, Y, V

# --- VISUALIZATION ---
st.subheader("🌪️ Airflow Distribution Map")

# Generate simulation data
X, Y, V = generate_sim_data(width, length, height, num_fans, fan_choice)

# Create heatmap
fig = go.Figure()

# Add heatmap
fig.add_trace(go.Heatmap(
    z=V,
    x=np.linspace(0, width, V.shape[1]),
    y=np.linspace(0, length, V.shape[0]),
    colorscale=[
        [0, 'darkblue'],
        [0.2, 'blue'],
        [0.4, 'cyan'],
        [0.6, 'yellow'],
        [0.8, 'orange'],
        [1, 'red']
    ],
    zmin=0,
    zmax=np.max(V) if np.max(V) > 0 else 1,
    colorbar=dict(
        title="Air Velocity<br>(normalized)",
        titleside="right"
    ),
    hovertemplate='X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Velocity: %{z:.2f}<extra></extra>'
))

# Add fan positions
fan_positions_x = []
fan_positions_y = []

if num_fans > 0:
    rows = int(np.sqrt(num_fans))
    cols = int(np.ceil(num_fans / rows))
    
    for i in range(num_fans):
        if cols > 0:
            fx = (i % cols + 0.5) * (width / cols)
        else:
            fx = width / 2
            
        if rows > 0:
            fy = (i // cols + 0.5) * (length / rows)
        else:
            fy = length / 2
        
        fan_positions_x.append(fx)
        fan_positions_y.append(fy)

# Add fan markers
fig.add_trace(go.Scatter(
    x=fan_positions_x,
    y=fan_positions_y,
    mode='markers+text',
    marker=dict(
        symbol='circle',
        size=15,
        color='white',
        line=dict(color='black', width=2)
    ),
    text=['💨' for _ in range(num_fans)],
    textposition="middle center",
    textfont=dict(size=12),
    name='Fan Positions',
    hovertext=[f'Fan {i+1}<br>Position: ({fan_positions_x[i]:.1f}, {fan_positions_y[i]:.1f})' 
               for i in range(num_fans)],
    hoverinfo='text'
))

# Add walls/obstacles (optional - can be customized)
# For demo, add some stall positions as examples
if app_type == "Hawker Center":
    # Add sample stall positions (just for visualization)
    stall_positions = [
        [width*0.25, length*0.25],
        [width*0.75, length*0.25],
        [width*0.25, length*0.75],
        [width*0.75, length*0.75]
    ]
    
    fig.add_trace(go.Scatter(
        x=[p[0] for p in stall_positions],
        y=[p[1] for p in stall_positions],
        mode='markers',
        marker=dict(
            symbol='square',
            size=20,
            color='brown',
            line=dict(color='black', width=1)
        ),
        name='Stalls',
        hovertext=[f'Stall {i+1}' for i in range(len(stall_positions))],
        hoverinfo='text'
    ))

fig.update_layout(
    title=f"Airflow Distribution - {fan_choice} ({num_fans} units)",
    xaxis_title="Width (meters)",
    yaxis_title="Length (meters)",
    height=600,
    hovermode='closest',
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(fig, use_container_width=True)

# --- ADDITIONAL ANALYTICS ---
st.subheader("📊 Performance Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    # Calculate average velocity in key areas
    avg_velocity = np.mean(V)
    st.metric(
        "Average Air Velocity",
        f"{avg_velocity:.2f} m/s",
        help="Mean air speed across the entire area"
    )

with col2:
    # Calculate coverage (areas with velocity > 0.3)
    threshold = 0.3
    coverage = np.sum(V > threshold) / V.size * 100
    st.metric(
        "Effective Coverage",
        f"{coverage:.1f}%",
        help=f"Area with velocity > {threshold} m/s"
    )

with col3:
    # Peak velocity
    peak_velocity = np.max(V)
    st.metric(
        "Peak Velocity",
        f"{peak_velocity:.2f} m/s",
        help="Maximum air speed detected"
    )

# --- RECOMMENDATIONS ---
st.subheader("💡 Optimization Recommendations")

recs = []

# Check ACH compliance
if ach_calculated < SS_553_TARGET_ACH:
    recs.append(f"❌ **Insufficient ACH**: Need {SS_553_TARGET_ACH - ach_calculated:.1f} more ACH")
    additional_fans = int((SS_553_TARGET_ACH - ach_calculated) / (FAN_SPECS[fan_choice]["cfm"] * 60 / volume_ft3))
    recs.append(f"   → Add {max(1, additional_fans)} more {fan_choice} units")

# Check coverage
if coverage < 60:
    recs.append(f"⚠️ **Poor coverage**: Only {coverage:.1f}% area effectively covered")
    recs.append("   → Consider repositioning fans or adding units in dead zones")

# Check velocity
if avg_velocity < 0.4:
    recs.append(f"⚠️ **Low average velocity**: {avg_velocity:.2f} m/s")
    recs.append("   → Consider higher CFM fans or additional units")
elif avg_velocity > 1.0:
    recs.append(f"ℹ️ **High velocity**: {avg_velocity:.2f} m/s")
    recs.append("   → May cause discomfort; consider reducing fan speed")

# Application-specific recommendations
app_rec = APP_RECOMMENDATIONS[app_type]
recs.append(f"💡 **{app_type} tip**: {app_rec['notes']}")

# Energy efficiency
cost_per_ach = est_monthly_cost / ach_calculated if ach_calculated > 0 else 0
if cost_per_ach > 10:
    recs.append(f"💰 **Energy efficiency**: Cost per ACH is ${cost_per_ach:.2f}")
    recs.append("   → Consider more efficient fan models")

# Display recommendations
for rec in recs:
    st.markdown(rec)

# --- EXPORT FUNCTIONALITY ---
st.subheader("📥 Export Report")

if st.button("Generate Report"):
    # Create report
    report = f"""
SG HAWKER AIRFLOW SIMULATION REPORT
====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROJECT DETAILS
--------------
Application: {app_type}
Dimensions: {width}m × {length}m × {height}m
Floor Area: {area_m2:.1f} m²
Volume: {volume_m3:.1f} m³

FAN CONFIGURATION
----------------
Fan Type: {fan_choice}
Number of Units: {num_fans}
Total Airflow: {total_cfm:,.0f} CFM
Total Power: {total_kw:.2f} kW
Mounting Type: {FAN_SPECS[fan_choice]['mounting']}
Noise Level: {FAN_SPECS[fan_choice]['noise_level']}

PERFORMANCE METRICS
------------------
Calculated ACH: {ach_calculated:.1f}
Target ACH (SS 553): {SS_553_TARGET_ACH}
Status: {'✅ COMPLIANT' if ach_calculated >= SS_553_TARGET_ACH else '❌ NON-COMPLIANT'}
Average Velocity: {avg_velocity:.2f} m/s
Coverage Area: {coverage:.1f}%
Peak Velocity: {peak_velocity:.2f} m/s

ENERGY COSTS
-----------
Daily Consumption: {daily_consumption:.2f} kWh
Monthly Consumption: {monthly_consumption:.2f} kWh
Monthly Cost: ${est_monthly_cost:.2f}
Electricity Rate: ${ELECTRICITY_RATE}/kWh

RECOMMENDATIONS
--------------
{chr(10).join(recs)}

---
Report generated by SG Hawker Airflow Simulator
For professional consultation, contact mechanical engineer.
    """
    
    st.download_button(
        label="Download Report (TXT)",
        data=report,
        file_name=f"airflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

# --- SS 553 REFERENCE ---
with st.expander("📚 About SS 553 Standard"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Singapore Standard SS 553:**
        - Code of Practice for Air-Conditioning and Mechanical Ventilation in Buildings
        - **Minimum ACH:** 20 air changes per hour for food establishments
        - **Purpose:** Ensure adequate ventilation for occupant health and comfort
        - **Scope:** Covers hawker centers, restaurants, canteens, and food courts
        """)
    
    with col2:
        st.markdown("""
        **Compliance Requirements:**
        - Regular testing and maintenance
        - Records of ventilation performance
        - Professional assessment recommended
        - Consider localised exhaust for cooking areas
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>🇸🇬 SG Hawker Airflow Simulator v2.0 | For preliminary design only | Always consult with mechanical engineers</small>
</div>
""", unsafe_allow_html=True)
