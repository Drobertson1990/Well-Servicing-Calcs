import streamlit as st
import math

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

STEEL_DENSITY = 7850  # kg/m3
GRAVITY = 9.81

# ---------------- SESSION STATE ----------------
if "settings" not in st.session_state:
    st.session_state.settings = {
        "rate_unit": "m/min",
        "force_unit": "daN",
        "theme": "Dark"
    }

if "well" not in st.session_state:
    st.session_state.well = {
        "job_name": "",
        "tvd": 0.0,
        "kop": 0.0,
        "td": 0.0,
        "liner_top": 0.0,
        "restrictions": [],
        "fluid_type": "Fresh Water",
        "fluid_density": 1000.0,
        "schematic": None
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
        "🧮 Engineering",
        "⚙️ Settings"
    ],
    label_visibility="collapsed"
)

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.header("Home")
    st.write("• Define well & fluid")
    st.write("• Build CT string")
    st.write("• Run engineering checks")
    st.success("Designed for fast, field-ready decisions.")

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

    st.session_state.well["liner_top"] = st.number_input(
        "Liner Top (m)", min_value=0.0
    )

    st.subheader("Restrictions")
    with st.expander("Add Restriction"):
        r_name = st.text_input("Name")
        r_depth = st.number_input("Depth (m)", min_value=0.0)
        r_id = st.number_input("ID (mm)", min_value=0.0)

        if st.button("Add Restriction"):
            st.session_state.well["restrictions"].append({
                "name": r_name,
                "depth": r_depth,
                "id_mm": r_id
            })

    for r in st.session_state.well["restrictions"]:
        st.write(f"{r['name']} @ {r['depth']} m | ID {r['id_mm']} mm")

    st.subheader("Fluid")
    fluid = st.selectbox("Fluid Type", ["Fresh Water", "Produced Water", "Custom"])

    if fluid == "Fresh Water":
        density = 1000
    elif fluid == "Produced Water":
        density = 1050
    else:
        density = st.number_input("Density (kg/m³)", min_value=0.0)

    st.session_state.well["fluid_type"] = fluid
    st.session_state.well["fluid_density"] = density
    st.success(f"Fluid Density: {density} kg/m³")

# ---------------- CT STRING BUILDER ----------------
elif page == "🧵 CT String Builder":
    st.header("CT String Builder (Whip → Core)")

    string_name = st.text_input("CT String Name")

    length = st.number_input("Section Length (m)", min_value=0.0)
    od = st.number_input("OD (mm)", min_value=0.0)
    wall = st.number_input("Wall (mm)", min_value=0.0)

    if st.button("Add Section"):
        st.session_state.ct_strings.setdefault(string_name, []).append({
            "length": length,
            "od": od,
            "wall": wall
        })

    if st.session_state.ct_strings:
        selected = st.selectbox(
            "Select String", list(st.session_state.ct_strings.keys())
        )

        total_length = 0
        total_volume = 0

        for i, sec in enumerate(st.session_state.ct_strings[selected]):
            id_mm = sec["od"] - 2 * sec["wall"]
            area = math.pi * ((id_mm / 2000) ** 2)
            volume = area * sec["length"]

            total_length += sec["length"]
            total_volume += volume

            st.write(
                f"Section {i+1}: {sec['length']} m | "
                f"OD {sec['od']} mm | Wall {sec['wall']} mm"
            )

        st.success(f"Total Length: {total_length:.1f} m")
        st.success(f"Total Volume: {total_volume:.3f} m³")

        st.subheader("Whip-End Trim")
        trim = st.number_input("Trim from whip end (m)", min_value=0.0)

        if st.button("Apply Trim"):
            if trim <= st.session_state.ct_strings[selected][0]["length"]:
                st.session_state.ct_strings[selected][0]["length"] -= trim
                st.success("Trim applied.")
            else:
                st.error("Trim exceeds first section length.")

# ---------------- ENGINEERING ----------------
elif page == "🧮 Engineering":
    st.header("Engineering Checks")

    # ---- Hydrostatic ----
    density = st.session_state.well["fluid_density"]
    tvd = st.session_state.well["tvd"]

    pressure_pa = density * GRAVITY * tvd
    st.subheader("Hydrostatic Pressure @ TVD")
    st.write(f"{pressure_pa/1000:.1f} kPa")
    st.write(f"{pressure_pa/1e6:.2f} MPa")
    st.write(f"{pressure_pa/6894.76:.1f} psi")

    # ---- Restriction Clearance ----
    if st.session_state.well["restrictions"] and st.session_state.ct_strings:
        min_id = min(r["id_mm"] for r in st.session_state.well["restrictions"])
        selected = list(st.session_state.ct_strings.keys())[0]
        max_od = max(sec["od"] for sec in st.session_state.ct_strings[selected])

        st.subheader("Restriction Clearance")

        if max_od < min_id:
            st.success("CT clears all restrictions.")
        else:
            st.error("CT OD exceeds restriction ID.")

    # ---- CT Length Check ----
    if st.session_state.ct_strings:
        selected = list(st.session_state.ct_strings.keys())[0]
        length = sum(sec["length"] for sec in st.session_state.ct_strings[selected])
        td = st.session_state.well["td"]

        st.subheader("CT Reach Check")

        if length >= td:
            st.success("CT string reaches TD.")
        else:
            st.error("CT string is too short.")

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
