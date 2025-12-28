import streamlit as st
import math

# =========================
# STATE
# =========================

def default_job():
    return {
        "ct": {
            "strings": [],
            "active_index": None
        },
        "well": {
            "tvd": None,
            "kop": None,
            "td": None,
            "casing": [],
            "restrictions": [],
            "schematic": None
        },
        "settings": {
            "units": "metric"
        }
    }

if "job" not in st.session_state:
    st.session_state.job = default_job()

job = st.session_state.job

# =========================
# APP CONFIG
# =========================

st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# =========================
# NAVIGATION
# =========================

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🧵 CT Strings",
        "🛢️ Well / Job",
        "🌀 Flow & Velocity",
        "🧊 Volumes",
    ]
)

# =========================
# HOME
# =========================

if page == "🏠 Home":
    st.title("Well Servicing Calculator")
    st.markdown("Field-ready calculations for coiled tubing operations.")

# =========================
# CT STRINGS (FIXED)
# =========================

elif page == "🧵 CT Strings":
    st.header("CT String Builder")

    # ---- CT OD OPTIONS ----
    ct_od_options = {
        '1" (25.4 mm)': 25.4,
        '1-1/4" (31.75 mm)': 31.75,
        '1-1/2" (38.10 mm)': 38.10,
        '1-3/4" (44.45 mm)': 44.45,
        '2" (50.8 mm)': 50.8,
        '2-3/8" (60.33 mm)': 60.33,
        '2-7/8" (73.03 mm)': 73.03,
    }

    # ---- Create new string ----
    string_name = st.text_input("CT String name", value="")

    if st.button("Create CT String"):
        if string_name.strip():
            job["ct"]["strings"].append({
                "name": string_name,
                "sections": []
            })
            job["ct"]["active_index"] = len(job["ct"]["strings"]) - 1

    if not job["ct"]["strings"]:
        st.info("Create a CT string to begin.")
        st.stop()

    # ---- Select active string ----
    names = [s["name"] for s in job["ct"]["strings"]]
    job["ct"]["active_index"] = st.selectbox(
        "Active CT String",
        range(len(names)),
        format_func=lambda i: names[i],
        index=job["ct"]["active_index"] or 0
    )

    active = job["ct"]["strings"][job["ct"]["active_index"]]

    st.markdown("### Add section (Whip → Core)")

    c1, c2, c3 = st.columns(3)

    with c1:
        length = st.number_input(
            "Section length (m)",
            min_value=0.0,
            value=None,
            placeholder="Enter length"
        )

    with c2:
        od_label = st.selectbox(
            "CT OD",
            list(ct_od_options.keys())
        )
        od_mm = ct_od_options[od_label]

    with c3:
        wall = st.number_input(
            "Wall thickness (mm)",
            min_value=0.0,
            value=None,
            placeholder="Enter wall thickness"
        )

    if st.button("Add section"):
        if length is not None and wall is not None:
            active["sections"].append({
                "length": length,
                "od": od_mm,
                "wall": wall
            })

    # ---- Display sections ----
    if active["sections"]:
        st.markdown("### Sections (Whip → Core)")

        total_length = 0.0
        total_volume = 0.0

        for i, sec in enumerate(active["sections"], start=1):
            id_mm = sec["od"] - 2 * sec["wall"]
            id_m = id_mm / 1000
            area = math.pi * (id_m / 2) ** 2
            volume = area * sec["length"]

            total_length += sec["length"]
            total_volume += volume

            st.write(
                f"Section {i}: "
                f"{sec['length']} m | "
                f"OD {sec['od']} mm | "
                f"Wall {sec['wall']} mm | "
                f"Volume {volume:.3f} m³"
            )

        st.success(f"Total Length: {total_length:.1f} m")
        st.success(f"Total Internal Volume: {total_volume:.3f} m³")

# =========================
# WELL / JOB
# =========================

elif page == "🛢️ Well / Job":
    st.header("Well / Job Geometry")

    c1, c2, c3 = st.columns(3)
    with c1:
        job["well"]["tvd"] = st.number_input("TVD (m)", value=job["well"]["tvd"])
    with c2:
        job["well"]["kop"] = st.number_input("KOP (m)", value=job["well"]["kop"])
    with c3:
        job["well"]["td"] = st.number_input("TD (m)", value=job["well"]["td"])

# =========================
# FLOW & VELOCITY
# =========================

elif page == "🌀 Flow & Velocity":
    st.header("Annular Velocity")
    st.info("Will be enabled once casing geometry is added.")

# =========================
# VOLUMES
# =========================

elif page == "🧊 Volumes":
    st.header("Volumes")
    st.info("Will auto-calculate from CT + well geometry.")
