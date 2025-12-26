import streamlit as st
import math

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------
if "settings" not in st.session_state:
    st.session_state.settings = {
        "length_unit": "m",
        "volume_unit": "m³",
        "rate_unit": "m/min",
        "force_unit": "daN",
        "theme": "Dark"
    }

if "well" not in st.session_state:
    st.session_state.well = {
        "job_name": "",
        "depth": 0.0,
        "fluid_density": 0.0,
        "schematic": None
    }

if "ct_strings" not in st.session_state:
    st.session_state.ct_strings = {}

if "active_ct_string" not in st.session_state:
    st.session_state.active_ct_string = None

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

st.markdown(
    """
Field-ready engineering calculations designed to:
- Save time
- Reduce errors
- Standardize job planning
"""
)

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
st.sidebar.header("Navigation")

page = st.sidebar.selectbox(
    "Go to",
    [
        "Home",
        "Well / Job Setup",
        "CT String Builder",
        "Annular Velocity",
        "Pipe Capacity",
        "Fluid Volumes",
        "Settings"
    ]
)

# ==================================================
# HOME
# ==================================================
if page == "Home":
    st.header("Home")

    st.markdown(
        """
### How this app works
1. **Set up your well / job**
2. **Build or select a CT string**
3. Run fast, repeatab
