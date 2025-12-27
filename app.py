import streamlit as st
import math

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# --------------------------------------------------
# SESSION STATE
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
    "Field-ready engineering calculations to save time, "
    "reduce errors, and standardize job planning."
)

# --------------------------------------------------
# SIDEBAR
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

# --------------------------------------------------
# HOME
# --------------------------------------------------
if page == "Home":
    st.header("Home")
    st.markdown(
        "- Set up your **well / job**\n"
        "- Build your **CT string**\n"
        "- Run fast, repeatable calculations\n\n"
        "Designed as a **field calculator**, not a spreadsheet."
    )

# --------------------------------------------------
# WELL / JOB SETUP
# --------------------------------------------------
elif page == "Well / Job Setup":
    st.header("Well / Job Setup")

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
        "Upload schematic",
        type=["png", "jpg", "jpeg", "pdf"]
    )

    if schematic:
        st.session_state.well["schematic"] = schematic

    if st.session_state.well["schematic"]:
        if st.session_state.well["schematic"].type == "application/pdf":
            st.info("PDF uploaded (display coming soon).")
        else:
            st.image(st.session_state.well["schematic"], use_column_width=True)

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
elif page == "Settings":
    st.header("Settings")

    st.session_state.settings["length_unit"] = st.selectbox(
        "Length unit", ["m", "ft"]
    )

    st.session_state.settings["volume_unit"] = st.selectbox(
        "Volume unit", ["m³", "bbl", "L"]
    )

    st.session_state.settings["rate_unit"] = st.selectbox(
        "Rate unit", ["m/min", "ft/min", "bbl/min"]
    )

    st.session_state.settings["force_unit"] = st.selectbox(
        "Force unit", ["daN", "lbf"]
    )

    st.session_state.settings["theme"] = st.selectbox(
        "Theme", ["Dark", "Light"]
    )

    st.success("Settings saved for this session.")

# --------------------------------------------------
# CT STRING BUILDER
# --------------------------------------------------
elif page == "CT String Builder":
    st.header("CT String Builder")
    st.markdown("Build CT strings **from whip end to core**.")

    string_name = st.text_input("CT String Name")

    col1, col2, col3 = st.columns(3)
    with col1:
        length_m = st.number_input("Section Length (m)", min_value=0.0)
    with col2:
        od_mm = st.number_input("OD (mm)", min_value=0.0)
    with col3:
        wall_mm = st.number_input("Wall Thickness (mm)", min_value=0.0)

    if st.button("Add Section"):
        if string_name and length_m > 0 and od_mm > 0 and wall_mm > 0:
            st.session_state.ct_strings.setdefault(string_name, []).append(
                {
                    "length_m": length_m,
                    "od_mm": od_mm,
                    "wall_mm": wall_mm
                }
            )
            st.success("Section added.")
        else:
            st.warning("Complete all fields.")

    if st.session_state.ct_strings:
        st.markdown("---")
        selected = st.selectbox(
            "Select CT String",
            list(st.session_state.ct_strings.keys())
        )

        sections = st.session_state.ct_strings[selected]
        total_length = 0.0
        total_volume = 0.0

        for i, sec in enumerate(sections, 1):
            id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
            id_m = id_mm / 1000
            area = math.pi * (id_m / 2) ** 2
            volume = area * sec["length_m"]

            total_length += sec["length_m"]
            total_volume += volume

            st.write(
                f"Section {i}: "
                f"{sec['length_m']} m | "
                f"OD {sec['od_mm']} mm | "
                f"Wall {sec['wall_mm']} mm | "
                f"Vol {volume:.3f} m³"
            )

        st.success(f"Total Length: {total_length:.1f} m")
        st.success(f"Total Internal Volume: {total_volume:.3f} m³")

# --------------------------------------------------
# ANNULAR VELOCITY
# --------------------------------------------------
elif page == "Annular Velocity":
    st.header("Annular Velocity")

    outer_id = st.number_input("Casing / Tubing ID (mm)", min_value=0.0)
    inner_od = st.number_input("CT OD (mm)", min_value=0.0)
    rate = st.number_input(
        f"Pump Rate ({st.session_state.settings['rate_unit']})",
        min_value=0.0
    )

    if outer_id > inner_od > 0:
        outer_area = math.pi * (outer_id / 2000) ** 2
        inner_area = math.pi * (inner_od / 2000) ** 2
        annular_area = outer_area - inner_area
        velocity = rate / annular_area

        st.success(
            f"Annular Velocity: {velocity:.2f} {st.session_state.settings['rate_unit']}"
        )
    else:
        st.warning("Outer ID must be larger than inner OD.")

# --------------------------------------------------
# PLACEHOLDERS
# --------------------------------------------------
elif page == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("Coming next.")

elif page == "Fluid Volumes":
    st.header("Fluid Volumes")
    st.info("Coming next.")
