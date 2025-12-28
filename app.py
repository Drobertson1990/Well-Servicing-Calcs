import streamlit as st
import math
from datetime import datetime

# =========================
# STATE
# =========================

def default_job():
    return {
        "meta": {
            "name": None,
            "last_modified": None
        },
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
        "fluids": {
            "base": None,
            "density": None,
            "chemicals": []
        },
        "settings": {
            "units": "metric",
            "flow_unit": "m/min",
            "force_unit": "daN",
            "theme": "dark"
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
        "⚙️ Settings"
    ]
)

# =========================
# HOME
# =========================

if page == "🏠 Home":
    st.title("Well Servicing Calculator")
    st.markdown("""
    **Field-ready engineering calculations**  
    Built for coiled tubing, service rigs, and snubbing.

    Use the menu on the left to:
    - Build CT strings
    - Define well geometry
    - Calculate volumes and velocities
    """)

# =========================
# CT STRINGS
# =========================

elif page == "🧵 CT Strings":
    st.header("CT String Builder")

    name = st.text_input("CT String name")

    st.subheader("Add section (Whip → Core)")

    c1, c2, c3 = st.columns(3)
    with c1:
        length = st.number_input("Length (m)", min_value=0.0)
    with c2:
        od = st.number_input("OD (mm)", min_value=0.0)
    with c3:
        wall = st.number_input("Wall thickness (mm)", min_value=0.0)

    if st.button("Add section"):
        if name and length > 0 and od > 0 and wall > 0:
            if not job["ct"]["strings"] or job["ct"]["strings"][-1]["name"] != name:
                job["ct"]["strings"].append({
                    "name": name,
                    "sections": []
                })
                job["ct"]["active_index"] = len(job["ct"]["strings"]) - 1

            job["ct"]["strings"][-1]["sections"].append({
                "length": length,
                "od": od,
                "wall": wall
            })

    if job["ct"]["strings"]:
        st.subheader("Saved CT Strings")

        names = [s["name"] for s in job["ct"]["strings"]]
        job["ct"]["active_index"] = st.selectbox(
            "Active CT String",
            range(len(names)),
            format_func=lambda i: names[i],
            index=job["ct"]["active_index"] if job["ct"]["active_index"] is not None else 0
        )

        active = job["ct"]["strings"][job["ct"]["active_index"]]

        total_len = 0
        total_vol = 0

        for i, sec in enumerate(active["sections"], start=1):
            id_mm = sec["od"] - 2 * sec["wall"]
            id_m = id_mm / 1000
            area = math.pi * (id_m / 2) ** 2
            vol = area * sec["length"]

            total_len += sec["length"]
            total_vol += vol

            st.write(
                f"Section {i}: {sec['length']} m | "
                f"OD {sec['od']} mm | Wall {sec['wall']} mm | "
                f"Volume {vol:.3f} m³"
            )

        st.success(f"Total Length: {total_len:.1f} m")
        st.success(f"Total Internal Volume: {total_vol:.3f} m³")

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

    st.subheader("Casing / Liner Sections")

    c1, c2, c3 = st.columns(3)
    with c1:
        top = st.number_input("Top depth (m)", min_value=0.0)
    with c2:
        bottom = st.number_input("Bottom depth (m)", min_value=0.0)
    with c3:
        id_mm = st.number_input("ID (mm)", min_value=0.0)

    if st.button("Add casing section"):
        if bottom > top and id_mm > 0:
            job["well"]["casing"].append({
                "top": top,
                "bottom": bottom,
                "id": id_mm
            })

    for c in job["well"]["casing"]:
        st.write(f"{c['top']}–{c['bottom']} m | ID {c['id']} mm")

    st.subheader("Restrictions")

    r1, r2 = st.columns(2)
    with r1:
        r_depth = st.number_input("Restriction depth (m)", min_value=0.0)
    with r2:
        r_id = st.number_input("Restriction ID (mm)", min_value=0.0)

    if st.button("Add restriction"):
        if r_id > 0:
            job["well"]["restrictions"].append({
                "depth": r_depth,
                "id": r_id
            })

    for r in job["well"]["restrictions"]:
        st.write(f"Depth {r['depth']} m | ID {r['id']} mm")

    st.subheader("Well Schematic")
    job["well"]["schematic"] = st.file_uploader(
        "Upload schematic",
        type=["png", "jpg", "jpeg", "pdf"]
    )

# =========================
# FLOW & VELOCITY
# =========================

elif page == "🌀 Flow & Velocity":
    st.header("Annular Velocity")

    if job["ct"]["active_index"] is None or not job["well"]["casing"]:
        st.info("Define CT string and casing geometry first.")
    else:
        depth = st.number_input("Depth (m)", min_value=0.0)
        rate = st.number_input("Pump rate (m³/min)", min_value=0.0)

        casing = next(
            (c for c in job["well"]["casing"] if c["top"] <= depth <= c["bottom"]),
            None
        )

        if casing:
            ct = job["ct"]["strings"][job["ct"]["active_index"]]
            last_sec = ct["sections"][0]

            ann_id_m = casing["id"] / 1000
            ct_od_m = last_sec["od"] / 1000

            ann_area = math.pi * ((ann_id_m / 2) ** 2 - (ct_od_m / 2) ** 2)
            velocity = rate / ann_area

            st.success(f"Annular Velocity: {velocity:.2f} m/min")
        else:
            st.warning("No casing section at this depth.")

# =========================
# VOLUMES
# =========================

elif page == "🧊 Volumes":
    st.header("Volumes")

    if job["ct"]["active_index"] is None or not job["well"]["casing"]:
        st.info("Define CT string and well geometry first.")
    else:
        ct = job["ct"]["strings"][job["ct"]["active_index"]]

        ct_vol = 0
        for sec in ct["sections"]:
            id_m = (sec["od"] - 2 * sec["wall"]) / 1000
            area = math.pi * (id_m / 2) ** 2
            ct_vol += area * sec["length"]

        ann_vol = 0
        for c in job["well"]["casing"]:
            ann_id_m = c["id"] / 1000
            ct_od_m = ct["sections"][0]["od"] / 1000
            ann_area = math.pi * ((ann_id_m / 2) ** 2 - (ct_od_m / 2) ** 2)
            ann_vol += ann_area * (c["bottom"] - c["top"])

        st.success(f"CT Internal Volume: {ct_vol:.3f} m³")
        st.success(f"Annular Volume: {ann_vol:.3f} m³")
        st.success(f"Total Circulating Volume: {(ct_vol + ann_vol):.3f} m³")

# =========================
# SETTINGS
# =========================

elif page == "⚙️ Settings":
    st.header("Settings")
    job["settings"]["theme"] = st.selectbox(
        "Theme", ["dark", "light"],
        index=0 if job["settings"]["theme"] == "dark" else 1
    )
