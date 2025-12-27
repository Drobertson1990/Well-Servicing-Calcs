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
    "Field-ready engineering calculations designed to save time, "
    "reduce errors, and standardize job planning."
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
    st.markdown("### How this app works")
    st.markdown(
        "- Set up your **well / job**\n"
        "- Build or select a **CT string**\n"
        "- Run fast, repeatable calculations\n\n"
        "This tool behaves like a **field calculator**, not a spreadsheet."
    )

# ==================================================
# WELL / JOB SETUP
# ==================================================
elif page == "Well / Job Setup":
    st.header("Well / Job Setup")

    st.subheader("Job Information")

    st.session_state.well["job_name"] = st.text_input(
        "Job / Well Name",
        st.session_state.well["job_name"]
    )

    st.session_state.well["depth"] = st.number_input(
        f"Total Depth ({st.session_state.settings['length_unit']})",
        min_value=0.0,
        value=st.session_state.well["depth"]
    )

    st.session_state.well["fluid_density"] = st.number_input(
        "Fluid Density (kg/m³)",
        min_value=0.0,
        value=st.session_state.well["fluid_density"]
    )

    st.subheader("Well Schematic")

    schematic = st.file_uploader(
        "Upload well schematic",
        type=["png", "jpg", "jpeg", "pdf"]
    )

    if schematic:
        st.session_state.well["schematic"] = schematic

    if st.session_state.well["schematic"]:
        if st.session_state.well["schematic"].type == "application/pdf":
            st.info("PDF uploaded. Display support coming soon.")
        else:
            st.image(st.session_state.well["schematic"], use_column_width=True)

# ==================================================
# SETTINGS
# ==================================================
elif page == "Settings":
    st.header("Settings")

    st.subheader("Units & Preferences")

    st.session_state.settings["length_unit"] = st.selectbox(
        "Length unit",
        ["m", "ft"],
        index=0 if st.session_state.settings["length_unit"] == "m" else 1
    )

    st.session_state.settings["volume_unit"] = st.selectbox(
        "Volume unit",
        ["m³", "bbl", "L"],
        index=["m³", "bbl", "L"].index(st.session_state.settings["volume_unit"])
    )

    st.session_state.settings["rate_unit"] = st.selectbox(
        "Rate unit",
        ["m/min", "ft/min", "bbl/min"],
        index=["m/min", "ft/min", "bbl/min"].index(st.session_state.settin_
