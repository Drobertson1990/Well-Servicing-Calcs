import streamlit as st
import math

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# ---------------- CONSTANTS ----------------
GRAVITY = 9.81

# ---------------- SESSION STATE ----------------
if "settings" not in st.session_state:
    st.session_state.settings = {
        "rate_unit": "m/min",
        "force_unit": "daN",
    }

if "well" not in st.session_state:
    st.session_state.well = {
        "job_name": "",
        "tvd": 0.0,
        "kop": 0.0,
        "td": 0.0,
        "liner_top": 0.0,
        "casing": [],   # depth-based casing/liner
        "fluid_density": 1000.0,
    }

if "ct_strings" not in st.session_state:
    st.session_state.ct_strings = {}

# ---------------- HEADER ----------------
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

# ---------------- SIDEBAR NAV ----------------
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🛢️ Well / Job",
        "🧵 CT String Builder",
        "🌀 Annular Velocity",
        "⚙️ Settings",
    ],
    label_visibility="collapsed",
)

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.header("Home")
    st.write("• Define well geometry")
    st.write("• Build CT string (whip → core)")
    st.write("• Calculate annular velocity using depth + rate only")
    st.success("Depth-based calculations. No re-entry of geometry.")

# ---------------- WELL / JOB ----------------
elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    st.session_state.well["job_name"] = st.text_input(
        "Job / Well Name", st.session_state.well["job_name"]
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.well["tvd"] = st.number_input("TVD (m)", min_value=0.0)
    with col2:
        st.session_state.well["kop"] = st.number_input("KOP (m)", min_value=0.0)
    with col3:
        st.session_state.well["td"] = st.number_input("TD (m)", min_value=0.0)

    st.subheader("Casing / Liner (Depth-Based)")
    st.caption("Define ALL casing or liner sections. No open hole.")

    with st.expander("Add Casing / Liner Section"):
        c_from = st.number_input("From depth (m)", min_value=0.0)
        c_to = st.number_input("To depth (m)", min_value=0.0)
        c_id = st.number_input("Internal Diameter (mm)", min_value=0.0)
        c_type = st.selectbox("Type", ["Casing", "Liner"])

        if st.button("Add Section"):
            if c_to > c_from and c_id > 0:
                st.session_state.well["casing"].append({
                    "from": c_from,
                    "to": c_to,
                    "id_mm": c_id,
                    "type": c_type,
                })
                st.success("Section added.")
            else:
                st.error("Invalid casing section.")

    if st.session_state.well["casing"]:
        st.markdown("**Defined Casing / Liner Sections:**")
        for i, c in enumerate(st.session_state.well["casing"], start=1):
            st.write(
                f"{i}. {c['type']} | {c['from']}–{c['to']} m | ID {c['id_mm']} mm"
            )

    st.subheader("Fluid")
    fluid = st.selectbox("Fluid Type", ["Fresh Water", "Produced Water", "Custom"])

    if fluid == "Fresh Water":
        density = 1000
    elif fluid == "Produced Water":
        density = 1050
    else:
        density = st.number_input("Density (kg/m³)", min_value=0.0)

    st.session_state.well["fluid_density"] = density
    st.success(f"Fluid Density: {density} kg/m³")

# ---------------- CT STRING BUILDER ----------------
elif page == "🧵 CT String Builder":
    st.header("CT String Builder (Whip → Core)")

    string_name = st.text_input("CT String Name")

    col1, col2, col3 = st.columns(3)
    with col1:
        length = st.number_input("Section Length (m)", min_value=0.0)
    with col2:
        od = st.number_input("OD (mm)", min_value=0.0)
    with col3:
        wall = st.number_input("Wall (mm)", min_value=0.0)

    if st.button("Add Section"):
        if string_name and length > 0 and od > 0 and wall > 0:
            st.session_state.ct_strings.setdefault(string_name, []).append({
                "length": length,
                "od": od,
                "wall": wall,
            })
            st.success("Section added.")
        else:
            st.error("Fill all fields and name the string.")

    if st.session_state.ct_strings:
        selected = st.selectbox("Select CT String", list(st.session_state.ct_strings.keys()))

        running_depth = 0.0
        st.markdown("**CT Sections (Whip → Core):**")

        for i, sec in enumerate(st.session_state.ct_strings[selected], start=1):
            running_depth += sec["length"]
            st.write(
                f"{i}. {sec['length']} m | OD {sec['od']} mm | "
                f"Wall {sec['wall']} mm | Reaches {running_depth:.1f} m"
            )

# ---------------- ANNULAR VELOCITY ----------------
elif page == "🌀 Annular Velocity":
    st.header("Annular Velocity (Depth-Based)")

    if not st.session_state.well["casing"]:
        st.warning("No casing defined. Add casing in Well / Job setup.")
        st.stop()

    if not st.session_state.ct_strings:
        st.warning("No CT string defined.")
        st.stop()

    selected_string = st.selectbox(
        "Active CT String", list(st.session_state.ct_strings.keys())
    )

    depth = st.number_input("Depth (m)", min_value=0.0)
    pump_rate = st.number_input("Pump Rate (m³/min)", min_value=0.0)

    # ---- Find casing at depth ----
    casing_section = None
    for c in st.session_state.well["casing"]:
        if c["from"] <= depth <= c["to"]:
            casing_section = c
            break

    if not casing_section:
        st.error("No casing defined at this depth.")
        st.stop()

    # ---- Find CT OD at depth ----
    ct_od = None
    depth_remaining = depth

    for sec in st.session_state.ct_strings[selected_string]:
        if depth_remaining <= sec["length"]:
            ct_od = sec["od"]
            break
        depth_remaining -= sec["length"]

    if ct_od is None:
        st.error("CT string does not reach this depth.")
        st.stop()

    # ---- Calculate Annular Velocity ----
    casing_area = math.pi * ((casing_section["id_mm"] / 2000) ** 2)
    ct_area = math.pi * ((ct_od / 2000) ** 2)
    annular_area = casing_area - ct_area

    if annular_area <= 0:
        st.error("Invalid annular geometry.")
        st.stop()

    velocity = pump_rate / annular_area

    st.subheader("Results")
    st.write(f"Active casing ID: {casing_section['id_mm']} mm")
    st.write(f"Active CT OD: {ct_od} mm")
    st.write(f"Annular area: {annular_area:.4f} m²")
    st.success(f"Annular Velocity: {velocity:.2f} m/min")

# ---------------- SETTINGS ----------------
elif page == "⚙️ Settings":
    st.header("Settings")

    st.session_state.settings["rate_unit"] = st.selectbox(
        "Rate Unit", ["m/min", "ft/min", "bbl/min"]
    )
    st.session_state.settings["force_unit"] = st.selectbox(
        "Force Unit", ["daN", "lbf"]
    )

    st.success("Settings saved.")
