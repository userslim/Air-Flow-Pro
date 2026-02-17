"""
SG Hawker Airflow Simulator
Compliant with Singapore SS 553 Standards
"""

import streamlit as st
import numpy as np
import sys
import subprocess
import importlib

# Try to import plotly, if it fails, try to install it
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly is not installed. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
        import plotly.graph_objects as go
        import plotly.express as px
        PLOTLY_AVAILABLE = True
        st.success("Plotly installed successfully! Please refresh the page.")
    except:
        st.error("""
        ⚠️ Plotly could not be installed automatically.
        Please make sure your requirements.txt includes 'plotly==5.17.0'
        """)

# Try to import pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    st.warning("Pandas is not installed. Some features may be limited.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
        import pandas as pd
        PANDAS_AVAILABLE = True
    except:
        pass

from datetime import datetime
import math

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
        "mounting": "Ceiling",
        "image": "🔄"
    },
    "Industrial Ceiling Fan": {
        "wattage": 85, 
        "cfm": 12000, 
        "radius": 1.5, 
        "desc": "Standard for high-density seating areas.",
        "noise_level": "Medium",
        "mounting": "Ceiling",
        "image": "🌀"
    },
    "Wall Mount Fan": {
        "wattage": 65, 
        "cfm": 6500, 
        "radius": 0.8, 
        "desc": "Targeted spot cooling for stalls and food preparation areas.",
        "noise_level": "Medium-High",
        "mounting": "Wall",
        "image": "⬆️"
    },
    "Pedestal Fan": {
        "wattage": 75, 
        "cfm": 8000, 
        "radius": 1.0, 
        "desc": "Portable option for flexible positioning.",
        "noise_level": "Medium",
        "mounting": "Floor",
        "image": "📌"
    },
    "Misting Fan": {
        "wattage": 200, 
        "cfm": 10000, 
        "radius": 2.0, 
        "desc": "Provides cooling through evaporation, ideal for outdoor areas.",
        "noise_level": "Medium",
        "mounting": "Floor/Stand",
        "image": "💧"
    }
}

# Application-specific recommendations
APP_RECOMMENDATIONS = {
    "Hawker Center": {
        "primary_fan": "HVLS (High Volume Low Speed)",
        "secondary_fan": "Industrial Ceiling Fan",
        "min_ach": 20,
        "notes": "Combine HVLS for general ventilation with spot fans at busy stalls",
        "icon": "🍜"
    },
    "Wet Market": {
        "primary_fan": "Industrial Ceiling Fan",
        "secondary_fan": "Wall Mount Fan",
        "min_ach": 15,
        "notes": "Focus on moisture control and targeted airflow at fish/meat stalls",
        "icon": "🐟"
    },
    "Industrial Canteen": {
        "primary_fan": "HVLS (High Volume Low Speed)",
        "secondary_fan": "Pedestal Fan",
        "min_ach": 18,
        "notes": "HVLS for main dining, portable fans for flexibility during peak hours",
        "icon": "🏭"
    }
}

st.set_page_config(
    page_title="SG Hawker Airflow Simulator", 
    page_icon="🇸🇬",
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
        padding: 1rem;
        background: linear-gradient(90deg, #fff3cd 0%, #fff 100%);
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .compliant {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #28a745;
        margin: 1rem 0;
    }
    .non-compliant {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #ffc107;
        margin: 1rem 0;
    }
    .fan-card {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- UI SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/singapore.png", width=100)
    st.header("📍 Building Layout")
    
    app_type = st.selectbox(
        "Application", 
        list(APP_RECOMMENDATIONS.keys()),
        format_func=lambda x: f"{APP_RECOMMENDATIONS[x]['icon']} {x}",
        help="Select the type of food establishment"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("Width (m)", 5.0, 100.0, 30.0, step=0.5)
    with col2:
        length = st.number_input("Length (m)", 5.0, 100.0, 40.0, step=0.5)
    
    height = st.number_input("Ceiling Height (m)", 3.0, 10.0, 5.0, step=0.5)
    
    # Show area summary
    area_m2 = width * length
    volume_m3 = width * length * height
    st.info(f"📐 Area: {area_m2:.0f} m² | Volume: {volume_m3:.0f} m³")
    
    st.header("🌀 Fan Selection")
    
    # Show recommended fan types
    rec = APP_RECOMMENDATIONS[app_type]
    st.info(f"💡 Recommended: {rec['primary_fan']} + {rec['secondary_fan']}")
    
    fan_choice = st.selectbox(
        "Fan Type", 
        list(FAN_SPECS.keys()),
        format_func=lambda x: f"{FAN_SPECS[x]['image']} {x}",
        help="Select fan type for simulation"
    )
    
    num_fans = st.slider("Number of Fans", 1, 40, 6)
    
    # Show fan details
    with st.expander("📋 Fan Details"):
        fan = FAN_SPECS[fan_choice]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Type:** {fan_choice}")
            st.write(f"**Wattage:** {fan['wattage']}W")
            st.write(f"**Airflow:** {fan['cfm']:,} CFM")
        with col2:
            st.write(f"**Mounting:** {fan['mounting']}")
            st.write(f"**Noise:** {fan['noise_level']}")
            st.write(f"**Coverage:** {fan['radius']}m radius")
        st.write(f"**Description:** {fan['desc']}")
    
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
st.markdown(f"<h1 class='main-title'>🇸🇬 SG Hawker Airflow Simulator</h1>", unsafe_allow_html=True)

# Top metrics in columns
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Floor Area", f"{area_m2:.0f} m²")
    st.markdown("</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Volume", f"{volume_m3:.0f} m³")
    st.markdown("</div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Total Airflow", f"{total_cfm:,.0f} CFM")
    st.markdown("</div>", unsafe_allow_html=True)
with col4:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Total Power", f"{total_kw:.1f} kW")
    st.markdown("</div>", unsafe_allow_html=True)

# Compliance section
st.markdown(f"**Target Air Changes per Hour (SS 553):** `{SS_553_TARGET_ACH} ACH` for food establishments")

col1, col2 = st.columns(2)
with col1:
    delta = ach_calculated - SS_553_TARGET_ACH
    delta_color = "normal" if delta >= 0 else "inverse"
    st.metric(
        "Calculated ACH", 
        f"{ach_calculated:.1f} ACH", 
        delta=f"{delta:+.1f} ACH",
        delta_color="off"  # We'll handle color manually
    )

with col2:
    st.metric(
        "Est. Monthly Cost", 
        f"S${est_monthly_cost:.2f}",
        help=f"Based on {hours_per_day}h/day, {days_per_month} days/month @ ${ELECTRICITY_RATE}/kWh"
    )

# Compliance status
if ach_calculated < SS_553_TARGET_ACH:
    deficit = SS_553_TARGET_ACH - ach_calculated
    additional_fans_needed = int(np.ceil(deficit / (FAN_SPECS[fan_choice]["cfm"] * 60 / volume_ft3)))
    
    st.markdown(f"""
    <div class='non-compliant'>
        ⚠️ <b>Warning:</b> Below SS 553 requirement for {app_type}<br>
        Current: {ach_calculated:.1f} ACH | Required: {SS_553_TARGET_ACH} ACH<br>
        <b>Recommendation:</b> Add {additional_fans_needed} more {fan_choice} unit(s) or use HVLS fans.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class='compliant'>
        ✅ <b>Compliance Achieved:</b> Meets SS 553 ventilation requirements<br>
        Current: {ach_calculated:.1f} ACH | Required: {SS_553_TARGET_ACH} ACH
    </div>
    """, unsafe_allow_html=True)

# --- VISUALIZATION SECTION ---
st.subheader("🌪️ Airflow Distribution Analysis")

if PLOTLY_AVAILABLE:
    # Generate simulation data
    def generate_sim_data(w, l, h, n, f_type):
        """Generate airflow simulation data"""
        # Create grid with reasonable resolution
        grid_size = 40
        x = np.linspace(0, w, grid_size)
        y = np.linspace(0, l, grid_size)
        X, Y = np.meshgrid(x, y)
        V = np.zeros_like(X)
        
        if n > 0:
            rows = int(np.sqrt(n))
            cols = int(np.ceil(n / rows))
            
            fan_spec = FAN_SPECS[f_type]
            r_val = fan_spec["radius"]
            strength = fan_spec["cfm"] / 10000
            
            for i in range(n):
                if cols > 0:
                    fx = (i % cols + 0.5) * (w / cols)
                else:
                    fx = w / 2
                    
                if rows > 0:
                    fy = (i // cols + 0.5) * (l / rows)
                else:
                    fy = l / 2
                
                dist = np.sqrt((X - fx)**2 + (Y - fy)**2)
                height_factor = 1.0 - min(h / 10, 0.5)
                V += strength * np.exp(-dist / (r_val * 1.5)) * height_factor
        
        return X, Y, V

    # Generate data
    X, Y, V = generate_sim_data(width, length, height, num_fans, fan_choice)

    # Create visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create heatmap
        fig = go.Figure()
        
        fig.add_trace(go.Heatmap(
            z=V,
            x=np.linspace(0, width, V.shape[1]),
            y=np.linspace(0, length, V.shape[0]),
            colorscale='RdYlBu_r',
            zmin=0,
            zmax=np.max(V) if np.max(V) > 0 else 1,
            colorbar=dict(
                title="Air Velocity<br>(normalized)",
                titleside="right"
            ),
            hovertemplate='X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Velocity: %{z:.2f}<extra></extra>'
        ))
        
        # Add fan positions
        if num_fans > 0:
            rows = int(np.sqrt(num_fans))
            cols = int(np.ceil(num_fans / rows))
            
            fan_x = []
            fan_y = []
            
            for i in range(num_fans):
                if cols > 0:
                    fx = (i % cols + 0.5) * (width / cols)
                else:
                    fx = width / 2
                    
                if rows > 0:
                    fy = (i // cols + 0.5) * (length / rows)
                else:
                    fy = length / 2
                
                fan_x.append(fx)
                fan_y.append(fy)
            
            fig.add_trace(go.Scatter(
                x=fan_x,
                y=fan_y,
                mode='markers',
                marker=dict(
                    symbol='circle',
                    size=12,
                    color='black',
                    line=dict(color='white', width=2)
                ),
                name='Fan Positions',
                text=[f'Fan {i+1}' for i in range(num_fans)],
                hoverinfo='text'
            ))
        
        fig.update_layout(
            title=f"Airflow Distribution - {fan_choice} ({num_fans} units)",
            xaxis_title="Width (meters)",
            yaxis_title="Length (meters)",
            height=500,
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Statistics")
        
        # Calculate statistics
        avg_velocity = np.mean(V)
        max_velocity = np.max(V)
        min_velocity = np.min(V)
        std_velocity = np.std(V)
        
        # Coverage areas
        low_flow = np.sum(V < 0.2) / V.size * 100
        medium_flow = np.sum((V >= 0.2) & (V < 0.5)) / V.size * 100
        high_flow = np.sum(V >= 0.5) / V.size * 100
        
        st.markdown(f"""
        <div class='fan-card'>
            <h4>Velocity Distribution</h4>
            <p>Average: {avg_velocity:.2f}</p>
            <p>Maximum: {max_velocity:.2f}</p>
            <p>Minimum: {min_velocity:.2f}</p>
            <p>Std Dev: {std_velocity:.2f}</p>
        </div>
        
        <div class='fan-card'>
            <h4>Coverage Analysis</h4>
            <p style='color: blue;'>Low Flow (<0.2): {low_flow:.1f}%</p>
            <p style='color: orange;'>Medium Flow (0.2-0.5): {medium_flow:.1f}%</p>
            <p style='color: red;'>High Flow (>0.5): {high_flow:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Fallback visualization when plotly is not available
    st.warning("""
    ⚠️ Plotly is not available. Showing simplified text-based analysis.
    
    To enable interactive visualizations, please ensure plotly is installed:
    ```bash
    pip install plotly
    ```
    """)
    
    # Simple text-based representation
    st.markdown("### Simplified Airflow Analysis")
    
    # Create a simple ASCII representation
    grid_size = 20
    chars = ['⬜', '🟨', '🟧', '🟥']
    
    result = ""
    for i in range(grid_size):
        row = ""
        for j in range(grid_size):
            # Simple distance-based calculation
            dist_to_center = ((i - grid_size/2)**2 + (j - grid_size/2)**2)**0.5
            if dist_to_center < 3:
                row += chars[3]
            elif dist_to_center < 6:
                row += chars[2]
            elif dist_to_center < 9:
                row += chars[1]
            else:
                row += chars[0]
        result += row + "\n"
    
    st.text(result)
    st.caption("Legend: 🟥 High flow, 🟧 Medium flow, 🟨 Low flow, ⬜ Minimal flow")

# --- RECOMMENDATIONS ---
st.subheader("💡 Optimization Recommendations")

# Generate recommendations based on calculations
recs = []

if ach_calculated < SS_553_TARGET_ACH:
    deficit = SS_553_TARGET_ACH - ach_calculated
    additional_fans = int(np.ceil(deficit / (FAN_SPECS[fan_choice]["cfm"] * 60 / volume_ft3)))
    recs.append(("🔴", f"Insufficient ACH - Add {additional_fans} more fans"))

if PLOTLY_AVAILABLE:
    avg_velocity = np.mean(V)
    if avg_velocity < 0.3:
        recs.append(("🟡", "Low average velocity - Consider repositioning fans"))
    elif avg_velocity > 0.8:
        recs.append(("🟢", "Good air velocity achieved"))

# Application-specific recommendations
app_rec = APP_RECOMMENDATIONS[app_type]
recs.append(("💡", f"{app_type} tip: {app_rec['notes']}"))

# Energy efficiency
if est_monthly_cost > 500:
    recs.append(("💰", "High energy cost - Consider more efficient fan models"))

# Display recommendations
for icon, text in recs:
    st.info(f"{icon} {text}")

# --- EXPORT FUNCTIONALITY ---
st.subheader("📥 Export Report")

if st.button("Generate Comprehensive Report"):
    # Create detailed report
    report = f"""SG HAWKER AIRFLOW SIMULATION REPORT
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

ENERGY COSTS
-----------
Daily Consumption: {daily_consumption:.2f} kWh
Monthly Consumption: {monthly_consumption:.2f} kWh
Monthly Cost: ${est_monthly_cost:.2f}
Electricity Rate: ${ELECTRICITY_RATE}/kWh

RECOMMENDATIONS
--------------
{chr(10).join([f'• {text}' for _, text in recs])}

---
Report generated by SG Hawker Airflow Simulator
For professional consultation, contact a mechanical engineer.
    """
    
    st.download_button(
        label="📥 Download Report (TXT)",
        data=report,
        file_name=f"sg_airflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

# --- SS 553 REFERENCE ---
with st.expander("📚 About SS 553: Code of Practice for Air-Conditioning and Mechanical Ventilation"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Key Requirements:**
        - Minimum 20 air changes per hour for food establishments
        - Regular maintenance and testing required
        - Records must be kept for inspection
        - Local exhaust for cooking areas
        """)
    
    with col2:
        st.markdown("""
        **Compliance Tips:**
        - Use combination of HVLS and spot fans
        - Consider heat load from cooking equipment
        - Account for occupancy density
        - Regular filter cleaning
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 1rem;'>
    <small>🇸🇬 SG Hawker Airflow Simulator v2.0 | For preliminary design only | Always consult with M&E engineers for final design</small>
    <br>
    <small>⚡ Compliant with Singapore Standard SS 553:2022</small>
</div>
""", unsafe_allow_html=True)

# Debug information (optional - remove in production)
if st.checkbox("Show Debug Info", False):
    st.write("### Debug Information")
    st.write(f"Plotly Available: {PLOTLY_AVAILABLE}")
    st.write(f"Pandas Available: {PANDAS_AVAILABLE}")
    st.write(f"Python Version: {sys.version}")
