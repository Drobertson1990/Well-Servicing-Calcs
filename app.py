import streamlit as st
import math

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# ---------------- CONSTANTS ----------------
GRAVITY = 9.81

CT_OD_PRESETS = {
    '1"': 25.4,
    '1¼"': 31.75,
    '1½"': 38.1,
    '1¾"': 44.45,
    '2"': 50.8,
    '2⅜"': 60.33,
    '2⅞"': 73.03,
}

# ---------------- SESSION STATE ----------------
if "settings" not in st.session_state:
    st.session_state.settings = {
        "rate_unit": "m/min",
        "force_unit": "daN",
    }

if "well" not in st.session_state:
    st.session_state.well = {
        "job_name": "",
        "tvd": None,
        "kop": None,
        "td": None,
        "casing": [],
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
    st.write("• Build CT string")
    st.write("• Depth-based annular velocity")
    st.success("Clean inputs. No default zeros.")

# ---------------- WELL / JOB ----------------
elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    st.session_state.well["job_name"] = st.text_input("Job / Well Name")

    col1, col2, col3 = st.columns(3)
    with col1:
        tvd = st.text_input("TVD (m)")
    with col2:
        kop = st.text_input("KOP (m)")
    with col3:
        td = st.text_input("TD (m)")

    try:
        st.session_state.well["tvd"] = float(tvd)
        st.session_state.well["kop"] = float(kop)
        st.session_state.well["td"] = float(td)
    except:
        pass

    st.subheader("Casing / Liner")

    with st.expander("Add Casing / Liner Section"):
        c_from = st.text_input("From depth (m)")
        c_to = st.text_input("To depth (m)")
        c_id = st.text_input("Internal Diameter (mm)")
        c_type = st.selectbox("Type", ["Casing", "Liner"])

        if st.button("Add Section"):
            try:
                st.session_state.well["casing"].append({
                    "from": float(c_from),
                    "to": float(c_to),
                    "id_mm": float(c_id),
                    "type": c_type,
                })
                st.success("Section added.")
            except:
                st.error("Invalid casing input.")

    for c in st.session_state.well["casing"]:
        st.write(
            f"{c['type']} | {c['from']}–{c['to']} m | ID {c['id_mm']} mm"
        )

    st.subheader("Fluid")
    fluid = st.selectbox("Fluid Type", ["Fresh Water", "Produced Water", "Custom"])

    if fluid == "Fresh Water":
        st.session_state.well["fluid_density"] = 1000
    elif fluid == "Produced Water":
        st.session_state.well["fluid_density"] = 1050
    else:
        density = st.text_input("Density (kg/m³)")
        try:
            st.session_state.well["fluid_density"] = float(density)
        except:
            pass

# ---------------- CT STRING BUILDER ----------------
elif page == "🧵 CT String Builder":
    st.header("CT String Builder (Whip → Core)")

    string_name = st.text_input("CT String Name")

    length = st.text_input("Section Length (m)")
    od_label = st.selectbox("CT OD", list(CT_OD_PRESETS.keys()))
    wall = st.text_input("Wall Thickness (mm)")

    if st.button("Add Section"):
        try:
            st.session_state.ct_strings.setdefault(string_name, []).append({
                "length": float(length),
                "od": CT_OD_PRESETS[od_label],
                "wall": float(wall),
            })
            st.success("Section added.")
        except:
            st.error("Invalid section input.")

    if st.session_state.ct_strings:
        selected = st.selectbox(
            "Select CT String", list(st.session_state.ct_strings.keys())
        )

        running = 0
        for i, sec in enumerate(st.session_state.ct_strings[selected], start=1):
            running += sec["length"]
            st.write(
                f"{i}. {sec['length']} m | "
                f"OD {sec['od']} mm | "
                f"Wall {sec['wall']} mm | "
                f"Reaches {running:.1f} m"
            )

# ---------------- ANNULAR VELOCITY ----------------
elif page == "🌀 Annular Velocity":
    st.header("Annular Velocity")

    depth = st.text_input("Depth (m)")
    rate = st.text_input("Pump Rate (m³/min)")

    try:
        depth = float(depth)
        rate = float(rate)
    except:
        st.warning("Enter depth and pump rate.")
        st.stop()

    casing = next(
        (c for c in st.session_state.well["casing"]
         if c["from"] <= depth <= c["to"]), None
    )

    if not casing:
        st.error("No casing defined at this depth.")
        st.stop()

    ct_od = None
    remaining = depth
    for sec in st.session_state.ct_strings[list(st.session_state.ct_strings.keys())[0]]:
        if remaining <= sec["length"]:
            ct_od = sec["od"]
            break
        remaining -= sec["length"]

    if not ct_od:
        st.error("CT does not reach depth.")
        st.stop()

    annular_area = (
        math.pi * ((casing["id_mm"] / 2000) ** 2)
        - math.pi * ((ct_od / 2000) ** 2)
    )

    velocity = rate / annular_area

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
