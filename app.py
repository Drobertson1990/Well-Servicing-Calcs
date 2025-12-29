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
    """)

# =========================
# CT STRINGS
# =========================

elif page == "🧵 CT Strings":
    st.header("CT String Builder")

    # ---- OD OPTIONS (LOCKED) ----
    ct_od_options = {
        '1" – 25.4 mm': 25.4,
        '1-1/4" – 31.8 mm': 31.8,
        '1-1/2" – 38.1 mm': 38.1,
        '1-3/4" – 44.5 mm': 44.5,
        '2" – 50.8 mm': 50.8,
        '2-3/8" – 60.3 mm': 60.3,
        '2-7/8" – 73.0 mm': 73.0
    }

    # ---- CREATE / SELECT STRING ----
    st.subheader("CT Strings")

    col1, col2 = st.columns([2, 1])

    with col1:
        new_name = st.text_input("Create new CT string", value="")

    with col2:
        if st.button("Add CT String"):
            if new_name.strip():
                job["ct"]["strings"].append({
                    "name": new_name.strip(),
                    "sections": []
                })
                job["ct"]["active_index"] = len(job["ct"]["strings"]) - 1

    if not job["ct"]["strings"]:
        st.info("Create a CT string to begin.")
        st.stop()

    names = [s["name"] for s in job["ct"]["strings"]]

    job["ct"]["active_index"] = st.selectbox(
        "Active CT String",
        range(len(names)),
        format_func=lambda i: names[i],
        index=job["ct"]["active_index"] if job["ct"]["active_index"] is not None else 0
    )

    ct = job["ct"]["strings"][job["ct"]["active_index"]]

    # ---- ADD SECTION (WHIP → CORE) ----
    st.markdown("### Add Section (Whip → Core)")

    c1, c2, c3 = st.columns(3)

    with c1:
        sec_length = st.number_input("Length (m)", min_value=0.0, value=None)

    with c2:
        sec_od_label = st.selectbox("OD", list(ct_od_options.keys()))

    with c3:
        sec_wall = st.number_input("Wall thickness (mm)", min_value=0.0, value=None)

    if st.button("Add Section"):
        if sec_length and sec_wall:
            ct["sections"].insert(0, {
                "length": sec_length,
                "od": ct_od_options[sec_od_label],
                "wall": sec_wall
            })
        else:
            st.warning("All section fields must be filled.")

    # ---- DISPLAY / EDIT SECTIONS ----
    if not ct["sections"]:
        st.info("No sections added yet.")
        st.stop()

    st.markdown("### Sections (Whip → Core)")

    total_length = 0.0
    internal_volume = 0.0
    displacement_volume = 0.0

    for i, sec in enumerate(ct["sections"]):
        id_mm = sec["od"] - 2 * sec["wall"]

        id_m = id_mm / 1000
        od_m = sec["od"] / 1000

        area_id = math.pi * (id_m / 2) ** 2
        area_od = math.pi * (od_m / 2) ** 2

        vol_internal = area_id * sec["length"]
        vol_disp = area_od * sec["length"]

        total_length += sec["length"]
        internal_volume += vol_internal
        displacement_volume += vol_disp

        with st.expander(f"Section {i+1} | {sec['length']} m | OD {sec['od']} mm"):
            st.write(f"Wall: {sec['wall']} mm")
            st.write(f"Internal volume: {vol_internal:.3f} m³")
            st.write(f"Displacement volume: {vol_disp:.3f} m³")

            trim = st.number_input(
                "Trim from whip end (m)",
                min_value=0.0,
                max_value=sec["length"],
                value=0.0,
                key=f"trim_{i}"
            )

            if st.button("Apply Trim", key=f"apply_trim_{i}"):
                sec["length"] -= trim

            if st.button("Delete Section", key=f"del_sec_{i}"):
                ct["sections"].pop(i)
                st.experimental_rerun()

    # ---- SUMMARY ----
    st.markdown("---")
    st.success(f"Total CT Length: {total_length:.1f} m")
    st.success(f"CT Internal Volume: {internal_volume:.3f} m³")
    st.success(f"CT Displacement Volume: {displacement_volume:.3f} m³")

    # ---- DELETE STRING ----
    if st.button("Delete Entire CT String"):
        job["ct"]["strings"].pop(job["ct"]["active_index"])
        job["ct"]["active_index"] = None
        st.experimental_rerun()
        
# =========================
# WELL / JOB (RESTORED & CORRECT)
# =========================

elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    # --- DEPTHS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        job["well"]["tvd"] = st.number_input("TVD (m)", value=job["well"]["tvd"])
    with c2:
        job["well"]["kop"] = st.number_input("KOP (m)", value=job["well"]["kop"])
    with c3:
        job["well"]["td"] = st.number_input("TD (m)", value=job["well"]["td"])

    # --- CASING / LINER ---
    st.subheader("Casing / Liner Sections")

    c1, c2, c3 = st.columns(3)
    with c1:
        top = st.number_input("Top depth (m)", min_value=0.0)
    with c2:
        bottom = st.number_input("Bottom depth (m)", min_value=0.0)
    with c3:
        id_mm = st.number_input("Internal diameter (mm)", min_value=0.0)

    if st.button("Add casing / liner section"):
        if bottom > top and id_mm > 0:
            job["well"]["casing"].append({
                "top": top,
                "bottom": bottom,
                "id": id_mm
            })

    for c in job["well"]["casing"]:
        st.write(f"{c['top']}–{c['bottom']} m | ID {c['id']} mm")

    # --- RESTRICTIONS ---
    st.subheader("Restrictions")

    r1, r2, r3 = st.columns(3)
    with r1:
        r_name = st.text_input("Restriction name (e.g. XN nipple)")
    with r2:
        r_depth = st.number_input("Restriction depth (m)", min_value=0.0)
    with r3:
        r_id = st.number_input("Restriction ID (mm)", min_value=0.0)

    if st.button("Add restriction"):
        if r_name and r_id > 0:
            job["well"]["restrictions"].append({
                "name": r_name,
                "depth": r_depth,
                "id": r_id
            })

    for r in job["well"]["restrictions"]:
        st.write(
            f"{r['name']} | Depth {r['depth']} m | ID {r['id']} mm"
        )

    # --- SCHEMATIC ---
    st.subheader("Well Schematic")
    job["well"]["schematic"] = st.file_uploader(
        "Upload schematic",
        type=["png", "jpg", "jpeg", "pdf"]
    )

# =========================
# FLOW & VELOCITY (UNCHANGED)
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
# VOLUMES (UNCHANGED)
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
        "Theme",
        ["dark", "light"],
        index=0 if job["settings"]["theme"] == "dark" else 1
    )
