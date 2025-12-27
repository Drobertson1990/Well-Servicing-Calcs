import streamlit as st
import math

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# ---------------- SESSION STATE ----------------
if "settings" not in st.session_state:
    st.session_state.settings = {
        "length_unit": "m",
        "volume_unit": "m3",
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

# ---------------- HEADER ----------------
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")
st.write("Field-ready engineering calculations for oilfield operations.")

# ---------------- SIDEBAR ----------------
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

# ---------------- HOME ----------------
if page == "Home":
    st.header("Home")
    st.write("1. Set up your well or job")
    st.write("2. Build your CT string")
    st.write("3. Run fast calculations")

# ---------------- WELL / JOB SETUP ----------------
elif page == "Well / Job Setup":
    st.header("Well / Job Setup")

    st.session_state.well["job_name"] = st.text_input(
        "Job / Well Name",
        st.session_state.well["job_name"]
    )

    st.session_state.well["depth"] = st.number_input(
        "Total Depth (m)",
        min_value=0.0,
        value=st.session_state.well["depth"]
    )

    st.session_state.well["fluid_density"] = st.number_input(
        "Fluid Density (kg/m3)",
        min_value=0.0,
        value=st.session_state.well["fluid_density"]
    )

    schematic = st.file_uploader(
        "Upload Well Schematic",
        type=["png", "jpg", "jpeg", "pdf"]
    )

    if schematic:
        st.session_state.well["schematic"] = schematic

    if st.session_state.well["schematic"]:
        if st.session_state.well["schematic"].type == "application/pdf":
            st.info("PDF uploaded (display coming later).")
        else:
            st.image(st.session_state.well["schematic"], use_column_width=True)

# ---------------- SETTINGS ----------------
elif page == "Settings":
    st.header("Settings")

    st.session_state.settings["length_unit"] = st.selectbox(
        "Length Unit", ["m", "ft"]
    )

    st.session_state.settings["volume_unit"] = st.selectbox(
        "Volume Unit", ["m3", "bbl", "L"]
    )

    st.session_state.settings["rate_unit"] = st.selectbox(
        "Rate Unit", ["m/min", "ft/min", "bbl/min"]
    )

    st.session_state.settings["force_unit"] = st.selectbox(
        "Force Unit", ["daN", "lbf"]
    )

    st.session_state.settings["theme"] = st.selectbox(
        "Theme", ["Dark", "Light"]
    )

    st.success("Settings saved for this session.")

# ---------------- CT STRING BUILDER ----------------
elif page == "CT String Builder":
    st.header("CT String Builder")
    st.write("Build CT strings from whip end to core.")

    string_name = st.text_input("CT String Name")

    length_m = st.number_input("Section Length (m)", min_value=0.0)
    od_mm = st.number_input("OD (mm)", min_value=0.0)
    wall_mm = st.number_input("Wall Thickness (mm)", min_value=0.0)

    if st.button("Add Section"):
        if string_name and length_m > 0 and od_mm > 0 and wall_mm > 0:
            st.session_state.ct_strings.setdefault(string_name, []).append({
                "length_m": length_m,
                "od_mm": od_mm,
                "wall_mm": wall_mm
            })
            st.success("Section added.")
        else:
            st.warning("Complete all fields.")

    if st.session_state.ct_strings:
        st.write("Saved CT Strings")
        selected = st.selectbox(
            "Select String",
            list(st.session_state.ct_strings.keys())
        )

        total_length = 0.0
        total_volume = 0.0

        for i, sec in enumerate(st.session_state.ct_strings[selected], 1):
            id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
            id_m = id_mm / 1000
            area = math.pi * (id_m / 2) ** 2
            volume = area * sec["length_m"]

            total_length += sec["length_m"]
            total_volume += volume

            st.write(
                "Section", i,
                "| Length:", sec["length_m"], "m",
                "| Volume:", round(volume, 3), "m3"
            )

        st.success("Total Length: " + str(round(total_length, 1)) + " m")
        st.success("Total Volume: " + str(round(total_volume, 3)) + " m3")

# ---------------- ANNULAR VELOCITY ----------------
elif page == "Annular Velocity":
    st.header("Annular Velocity")

    casing_id = st.number_input("Casing / Tubing ID (mm)", min_value=0.0)
    ct_od = st.number_input("CT OD (mm)", min_value=0.0)
    rate = st.number_input("Pump Rate", min_value=0.0)

    if casing_id > ct_od > 0:
        outer_area = math.pi * (casing_id / 2000) ** 2
        inner_area = math.pi * (ct_od / 2000) ** 2
        annular_area = outer_area - inner_area
        velocity = rate / annular_area
        st.success("Annular Velocity: " + str(round(velocity, 2)))
    else:
        st.warning("Casing ID must be greater than CT OD.")

# ---------------- PLACEHOLDERS ----------------
elif page == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("Coming soon.")

elif page == "Fluid Volumes":
    st.header("Fluid Volumes")
    st.info("Coming soon.")
