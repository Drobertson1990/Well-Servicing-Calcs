import streamlit as st
import math
import pandas as pd

# -------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------
if "ct_strings" not in st.session_state:
    st.session_state.ct_strings = {}

if "active_ct" not in st.session_state:
    st.session_state.active_ct = None

if "well" not in st.session_state:
    st.session_state.well = {
        "TVD": None,
        "KOP": None,
        "TD": None,
        "casing": [],
        "restrictions": []
    }

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Home",
        "🧵 CT Strings",
        "🛢️ Well / Job",
        "🌀 Flow & Velocity",
        "🧊 Volumes",
        "⚙️ Settings"
    ]
)

# -------------------------------------------------
# HOME
# -------------------------------------------------
if page == "🏠 Home":
    st.title("Well Servicing Calculator")
    st.markdown("""
    **Field-ready calculations for CT, service rigs, and snubbing.**

    • Geometry-driven  
    • Error-resistant  
    • Built for supervisors & engineers  
    """)

# -------------------------------------------------
# CT STRING BUILDER
# -------------------------------------------------
elif page == "🧵 CT Strings":
    st.title("CT String Builder")

    CT_OD_OPTIONS = {
        '1" – 25.4 mm': 25.4,
        '1.25" – 31.8 mm': 31.8,
        '1.5" – 38.1 mm': 38.1,
        '1.75" – 44.5 mm': 44.5,
        '2" – 50.8 mm': 50.8,
        '2.375" – 60.3 mm': 60.3,
        '2.875" – 73.0 mm': 73.0
    }

    string_name = st.text_input("CT String Name")

    st.subheader("Add Section (Whip → Core order)")

    col1, col2, col3 = st.columns(3)
    with col1:
        length_m = st.number_input("Section Length (m)", min_value=0.0, value=None)
    with col2:
        od_label = st.selectbox("CT OD", list(CT_OD_OPTIONS.keys()))
        od_mm = CT_OD_OPTIONS[od_label]
    with col3:
        wall_mm = st.number_input("Wall Thickness (mm)", min_value=0.0, value=None)

    if st.button("Add Section"):
        if string_name and length_m and wall_mm:
            section = {
                "length": length_m,
                "od": od_mm,
                "wall": wall_mm
            }
            st.session_state.ct_strings.setdefault(string_name, []).append(section)
            st.session_state.active_ct = string_name

    if st.session_state.ct_strings:
        st.subheader("Saved CT Strings")
        active = st.selectbox(
            "Active CT String",
            st.session_state.ct_strings.keys(),
            index=list(st.session_state.ct_strings.keys()).index(st.session_state.active_ct)
            if st.session_state.active_ct in st.session_state.ct_strings else 0
        )
        st.session_state.active_ct = active

        total_length = 0
        total_volume = 0

        for i, sec in enumerate(st.session_state.ct_strings[active]):
            id_mm = sec["od"] - 2 * sec["wall"]
            id_m = id_mm / 1000
            area = math.pi * (id_m / 2) ** 2
            vol = area * sec["length"]

            total_length += sec["length"]
            total_volume += vol

            st.write(
                f"Section {i+1}: {sec['length']} m | OD {sec['od']} mm | Wall {sec['wall']} mm"
            )

        st.success(f"Total Length: {total_length:.1f} m")
        st.success(f"Internal Volume: {total_volume:.3f} m³")

# -------------------------------------------------
# WELL / JOB
# -------------------------------------------------
elif page == "🛢️ Well / Job":
    st.title("Well / Job Setup")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.well["TVD"] = st.number_input("TVD (m)", value=None)
    with col2:
        st.session_state.well["KOP"] = st.number_input("KOP (m)", value=None)
    with col3:
        st.session_state.well["TD"] = st.number_input("TD (m)", value=None)

    st.subheader("Casing / Liner")
    casing_od = st.number_input("Casing ID (mm)", value=None)
    casing_td = st.number_input("Casing Shoe Depth (m)", value=None)

    if st.button("Add Casing"):
        if casing_od and casing_td:
            st.session_state.well["casing"].append(
                {"id": casing_od, "td": casing_td}
            )

    st.subheader("Restrictions")
    r_name = st.text_input("Restriction Name")
    r_id = st.number_input("Restriction ID (mm)", value=None)
    r_depth = st.number_input("Restriction Depth (m)", value=None)

    if st.button("Add Restriction"):
        if r_name and r_id and r_depth:
            st.session_state.well["restrictions"].append(
                {"name": r_name, "id": r_id, "depth": r_depth}
            )

    st.subheader("Well Schematic")
    schematic = st.file_uploader("Upload schematic", type=["png", "jpg", "pdf"])
    if schematic:
        st.image(schematic, use_column_width=True)

# -------------------------------------------------
# FLOW & VELOCITY
# -------------------------------------------------
elif page == "🌀 Flow & Velocity":
    st.title("Annular Velocity")

    if not st.session_state.active_ct or not st.session_state.well["casing"]:
        st.warning("Select CT string and casing first.")
    else:
        depth = st.number_input("Depth (m)", value=None)
        rate = st.number_input("Pump Rate (m³/min)", value=None)

        ct = st.session_state.ct_strings[st.session_state.active_ct][0]
        casing = st.session_state.well["casing"][-1]

        if depth and rate:
            casing_area = math.pi * (casing["id"] / 2000) ** 2
            ct_area = math.pi * (ct["od"] / 2000) ** 2
            ann_area = casing_area - ct_area

            vel = rate / ann_area
            circ_time = depth / vel

            st.success(f"Annular Velocity: {vel:.2f} m/min")
            st.success(f"Circulation Time: {circ_time:.1f} min")

# -------------------------------------------------
# VOLUMES
# -------------------------------------------------
elif page == "🧊 Volumes":
    st.title("Volumes")

    if not st.session_state.active_ct or not st.session_state.well["casing"]:
        st.warning("CT string and well data required.")
    else:
        ct = st.session_state.ct_strings[st.session_state.active_ct]
        casing = st.session_state.well["casing"][-1]

        ct_internal = 0
        ct_displacement = 0

        for sec in ct:
            id_mm = sec["od"] - 2 * sec["wall"]
            id_area = math.pi * (id_mm / 2000) ** 2
            od_area = math.pi * (sec["od"] / 2000) ** 2

            ct_internal += id_area * sec["length"]
            ct_displacement += od_area * sec["length"]

        hole_area = math.pi * (casing["id"] / 2000) ** 2
        hole_vol = hole_area * st.session_state.well["TD"]

        annular_vol = hole_vol - ct_displacement

        st.success(f"CT Internal Volume: {ct_internal:.3f} m³")
        st.success(f"CT Displacement: {ct_displacement:.3f} m³")
        st.success(f"Annular Volume: {annular_vol:.3f} m³")
        st.success(f"Total Circulating Volume: {(ct_internal + annular_vol):.3f} m³")

# -------------------------------------------------
# SETTINGS
# -------------------------------------------------
elif page == "⚙️ Settings":
    st.title("Settings")
    st.info("Units, display preferences, and themes will live here.")
