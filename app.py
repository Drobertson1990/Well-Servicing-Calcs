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
        "🧊 Volumes",
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
    st.write("• Depth-based volumes")
    st.success("All volumes are geometry-driven.")

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

    if not ct_od:
        st.error("CT does not reach depth.")
        st.stop()

    annular_area = (
        math.pi * ((casing["id_mm"] / 2000) ** 2)
        - math.pi * ((ct_od / 2000) ** 2)
    )

    velocity = rate / annular_area
    st.success(f"Annular Velocity: {velocity:.2f} m/min")

# ---------------- VOLUMES ----------------
elif page == "🧊 Volumes":
    st.header("Volumes (Depth-Based)")

    depth = st.text_input("Depth (m)")

    try:
        depth = float(depth)
    except:
        st.warning("Enter depth.")
        st.stop()

    if not st.session_state.ct_strings or not st.session_state.well["casing"]:
        st.error("CT string and casing must be defined.")
        st.stop()

    ct_string = list(st.session_state.ct_strings.values())[0]

    # ---- CT INTERNAL VOLUME ----
    ct_vol = 0.0
    remaining = depth

    for sec in ct_string:
        id_mm = sec["od"] - 2 * sec["wall"]
        area = math.pi * ((id_mm / 2000) ** 2)

        length = min(sec["length"], remaining)
        ct_vol += area * length
        remaining -= length

        if remaining <= 0:
            break

    # ---- ANNULAR VOLUME ----
    ann_vol = 0.0
    remaining = depth

    for sec in ct_string:
        ct_od = sec["od"]
        sec_len = min(sec["length"], remaining)

        casing = next(
            (c for c in st.session_state.well["casing"]
             if c["from"] <= (depth - remaining + 0.01) <= c["to"]), None
        )

        if not casing:
            st.error("Missing casing for annular volume.")
            st.stop()

        casing_area = math.pi * ((casing["id_mm"] / 2000) ** 2)
        ct_area = math.pi * ((ct_od / 2000) ** 2)

        ann_vol += (casing_area - ct_area) * sec_len
        remaining -= sec_len

        if remaining <= 0:
            break

    st.subheader("Results")

    st.write(f"CT Internal Volume: {ct_vol:.3f} m³")
    st.write(f"Annular Volume: {ann_vol:.3f} m³")
    st.success(f"Total Circulating Volume: {(ct_vol + ann_vol):.3f} m³")

    st.caption("Conversions")
    st.write(f"CT Volume: {ct_vol * 6.2898:.2f} bbl | {ct_vol * 1000:.0f} L")
    st.write(f"Annular Volume: {ann_vol * 6.2898:.2f} bbl | {ann_vol * 1000:.0f} L")

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
