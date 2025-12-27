import streamlit as st
import math

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# ---------------- CONSTANTS ----------------
CT_OD_PRESETS = {
    '1"': 25.4,
    '1¼"': 31.75,
    '1½"': 38.1,
    '1¾"': 44.45,
    '2"': 50.8,
    '2⅜"': 60.33,
    '2⅞"': 73.03,
}

FRESH_WATER_DENSITY = 1000.0      # kg/m³
PRODUCED_WATER_DENSITY = 1080.0   # kg/m³ (typical)

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
    }

if "ct_strings" not in st.session_state:
    st.session_state.ct_strings = {}

if "fluid" not in st.session_state:
    st.session_state.fluid = {
        "base_type": "Fresh Water",
        "base_density": FRESH_WATER_DENSITY,
        "chemicals": [],
    }

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
        "🧊 Volumes",
        "🧪 Fluids & Chemicals",
        "⚙️ Settings",
    ],
    label_visibility="collapsed",
)

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.header("Home")
    st.write("• Geometry-driven calculations")
    st.write("• CT + casing linked volumes")
    st.write("• Real-time fluid blending")
    st.success("Field-ready logic. No guesswork.")

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
    ct_string = list(st.session_state.ct_strings.values())[0]

    for sec in ct_string:
        if remaining <= sec["length"]:
            ct_od = sec["od"]
            break
        remaining -= sec["length"]

    annular_area = (
        math.pi * ((casing["id_mm"] / 2000) ** 2)
        - math.pi * ((ct_od / 2000) ** 2)
    )

    velocity = rate / annular_area
    st.success(f"Annular Velocity: {velocity:.2f} m/min")

# ---------------- VOLUMES ----------------
elif page == "🧊 Volumes":
    st.header("Volumes")

    depth = st.text_input("Depth (m)")
    try:
        depth = float(depth)
    except:
        st.warning("Enter depth.")
        st.stop()

    ct_string = list(st.session_state.ct_strings.values())[0]

    ct_vol = 0
    ann_vol = 0
    remaining = depth

    for sec in ct_string:
        id_mm = sec["od"] - 2 * sec["wall"]
        ct_area = math.pi * ((id_mm / 2000) ** 2)

        casing = next(
            (c for c in st.session_state.well["casing"]
             if c["from"] <= (depth - remaining + 0.01) <= c["to"]), None
        )

        casing_area = math.pi * ((casing["id_mm"] / 2000) ** 2)

        length = min(sec["length"], remaining)
        ct_vol += ct_area * length
        ann_vol += (casing_area - math.pi * ((sec["od"] / 2000) ** 2)) * length
        remaining -= length

        if remaining <= 0:
            break

    st.write(f"CT Internal Volume: {ct_vol:.3f} m³")
    st.write(f"Annular Volume: {ann_vol:.3f} m³")
    st.success(f"Total Circulating Volume: {(ct_vol + ann_vol):.3f} m³")

# ---------------- FLUIDS & CHEMICALS ----------------
elif page == "🧪 Fluids & Chemicals":
    st.header("Fluids & Chemicals")

    base = st.selectbox(
        "Base Fluid",
        ["Fresh Water", "Produced Water", "Custom"]
    )

    if base == "Fresh Water":
        base_density = FRESH_WATER_DENSITY
    elif base == "Produced Water":
        base_density = PRODUCED_WATER_DENSITY
    else:
        base_density = st.number_input("Custom Density (kg/m³)", min_value=800.0)

    st.session_state.fluid["base_density"] = base_density

    st.subheader("Add Chemical")

    chem_name = st.text_input("Chemical Name")
    chem_density = st.number_input("Chemical Density (kg/m³)", min_value=500.0)
    chem_rate = st.number_input("Mixing Rate (L/m³)", min_value=0.0)

    if st.button("Add Chemical"):
        st.session_state.fluid["chemicals"].append({
            "name": chem_name,
            "density": chem_density,
            "rate": chem_rate,
        })
        st.success("Chemical added.")

    total_rate = sum(c["rate"] for c in st.session_state.fluid["chemicals"])
    weighted_density = (
        (base_density * (1000 - total_rate))
        + sum(c["density"] * c["rate"] for c in st.session_state.fluid["chemicals"])
    ) / 1000

    st.subheader("Blended Fluid Properties")
    st.write(f"Base Density: {base_density:.1f} kg/m³")
    st.write(f"Chemical Volume: {total_rate:.1f} L/m³")
    st.success(f"Final Blended Density: {weighted_density:.1f} kg/m³")

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
