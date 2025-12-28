import streamlit as st
import math

# =========================
# APP CONFIG
# =========================
st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# =========================
# GLOBAL JOB STATE
# =========================
if "job" not in st.session_state:
    st.session_state.job = {
        "ct_strings": {},
        "active_ct": None,
        "well": {
            "geometry": {
                "TVD_m": None,
                "KOP_m": None,
                "TD_m": None
            },
            "casing": [],
            "restrictions": [],
            "schematic": None
        }
    }

# =========================
# CONSTANTS
# =========================
CT_OD_OPTIONS = {
    '1" – 25.4 mm': 25.4,
    '1.25" – 31.8 mm': 31.8,
    '1.5" – 38.1 mm': 38.1,
    '1.75" – 44.5 mm': 44.5,
    '2" – 50.8 mm': 50.8,
    '2.375" – 60.3 mm': 60.3,
    '2.875" – 73.0 mm': 73.0
}

# =========================
# HELPER FUNCTIONS (CT)
# =========================
def calc_internal_volume(sections):
    vol = 0
    for s in sections:
        id_mm = s["od_mm"] - 2 * s["wall_mm"]
        id_m = id_mm / 1000
        area = math.pi * (id_m / 2) ** 2
        vol += area * s["length_m"]
    return vol

def calc_displacement(sections):
    disp = 0
    for s in sections:
        od_m = s["od_mm"] / 1000
        id_m = (s["od_mm"] - 2 * s["wall_mm"]) / 1000
        area = math.pi * ((od_m / 2) ** 2 - (id_m / 2) ** 2)
        disp += area * s["length_m"]
    return disp

def calc_total_length(sections):
    return sum(s["length_m"] for s in sections)

def calc_ratings_placeholder():
    return {
        "burst_80": "TBD",
        "collapse_80": "TBD",
        "max_pull_80": "TBD"
    }

# =========================
# HEADER
# =========================
st.title("Well Servicing Calculator")
st.subheader("Phase 1–2 | CT Strings + Well / Job")

# =========================
# SIDEBAR NAV
# =========================
st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "🧵 CT Strings", "🛢️ Well / Job"]
)

# =========================
# HOME
# =========================
if page == "🏠 Home":
    st.header("Home")

    if st.session_state.job["active_ct"]:
        st.success(f"Active CT String: {st.session_state.job['active_ct']}")
    else:
        st.warning("No active CT string selected.")

    geo = st.session_state.job["well"]["geometry"]
    if geo["TD_m"]:
        st.info(f"Well TD: {geo['TD_m']} m")

# =========================
# CT STRINGS (UNCHANGED)
# =========================
if page == "🧵 CT Strings":
    st.header("CT String Builder")

    col1, col2 = st.columns(2)

    with col1:
        new_string = st.text_input("Create new CT string")
        if st.button("Create CT String"):
            if new_string:
                st.session_state.job["ct_strings"][new_string] = {
                    "sections": [],
                    "ratings": calc_ratings_placeholder()
                }
                st.session_state.job["active_ct"] = new_string

    with col2:
        if st.session_state.job["ct_strings"]:
            active = st.selectbox(
                "Select active CT string",
                list(st.session_state.job["ct_strings"].keys()),
                index=list(st.session_state.job["ct_strings"].keys()).index(
                    st.session_state.job["active_ct"]
                ) if st.session_state.job["active_ct"] else 0
            )
            st.session_state.job["active_ct"] = active

    if st.session_state.job["active_ct"]:
        st.subheader("Add Section (Whip → Core)")
        c1, c2, c3 = st.columns(3)

        with c1:
            length_m = st.number_input("Length (m)", min_value=0.0)
        with c2:
            od_label = st.selectbox("OD", list(CT_OD_OPTIONS.keys()))
            od_mm = CT_OD_OPTIONS[od_label]
        with c3:
            wall_mm = st.number_input("Wall thickness (mm)", min_value=0.0)

        if st.button("Add Section"):
            if length_m > 0 and wall_mm > 0:
                st.session_state.job["ct_strings"][st.session_state.job["active_ct"]]["sections"].append(
                    {"length_m": length_m, "od_mm": od_mm, "wall_mm": wall_mm}
                )

        sections = st.session_state.job["ct_strings"][st.session_state.job["active_ct"]]["sections"]

        if sections:
            st.subheader("Sections (Whip → Core)")
            for i, s in enumerate(sections):
                st.write(
                    f"{i+1}. {s['length_m']} m | OD {s['od_mm']} mm | Wall {s['wall_mm']} mm"
                )

            st.subheader("Trim Whip End")
            trim_len = st.number_input("Trim length (m)", min_value=0.0)
            if st.button("Trim"):
                remaining = trim_len
                new_sections = []
                for s in sections:
                    if remaining <= 0:
                        new_sections.append(s)
                    elif s["length_m"] > remaining:
                        s["length_m"] -= remaining
                        new_sections.append(s)
                        remaining = 0
                    else:
                        remaining -= s["length_m"]
                st.session_state.job["ct_strings"][st.session_state.job["active_ct"]]["sections"] = new_sections

            st.subheader("Calculated")
            st.metric("Total Length (m)", f"{calc_total_length(sections):.1f}")
            st.metric("Internal Volume (m³)", f"{calc_internal_volume(sections):.3f}")
            st.metric("Displacement (m³)", f"{calc_displacement(sections):.3f}")

# =========================
# WELL / JOB SETUP (CORRECTED)
# =========================
if page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    # WELL GEOMETRY
    st.subheader("Well Geometry")
    geo = st.session_state.job["well"]["geometry"]

    g1, g2, g3 = st.columns(3)
    with g1:
        geo["TVD_m"] = st.number_input("TVD (m)", value=geo["TVD_m"])
    with g2:
        geo["KOP_m"] = st.number_input("KOP (m)", value=geo["KOP_m"])
    with g3:
        geo["TD_m"] = st.number_input("TD (m)", value=geo["TD_m"])

    st.markdown("---")

    # CASING / LINER
    st.subheader("Casing / Liner")

    c1, c2, c3 = st.columns(3)
    with c1:
        casing_name = st.text_input("Section name (optional)")
    with c2:
        casing_id = st.number_input("ID (mm)", min_value=0.0)
    with c3:
        shoe_depth = st.number_input("Shoe depth (m)", min_value=0.0)

    if st.button("Add Casing / Liner"):
        if casing_id > 0 and shoe_depth > 0:
            st.session_state.job["well"]["casing"].append({
                "name": casing_name,
                "id_mm": casing_id,
                "shoe_depth_m": shoe_depth
            })

    if st.session_state.job["well"]["casing"]:
        h1, h2, h3 = st.columns(3)
        h1.markdown("**Name**")
        h2.markdown("**ID (mm)**")
        h3.markdown("**Shoe depth (m)**")

        for c in st.session_state.job["well"]["casing"]:
            r1, r2, r3 = st.columns(3)
            r1.write(c["name"] if c["name"] else "—")
            r2.write(c["id_mm"])
            r3.write(c["shoe_depth_m"])

    st.markdown("---")

    # RESTRICTIONS
    st.subheader("Restrictions")

    r1, r2, r3 = st.columns(3)
    with r1:
        r_name = st.text_input("Restriction name")
    with r2:
        r_id = st.number_input("Restriction ID (mm)", min_value=0.0)
    with r3:
        r_depth = st.number_input("Restriction depth (m)", min_value=0.0)

    if st.button("Add Restriction"):
        if r_name and r_id > 0 and r_depth > 0:
            st.session_state.job["well"]["restrictions"].append({
                "name": r_name,
                "id_mm": r_id,
                "depth_m": r_depth
            })

    if st.session_state.job["well"]["restrictions"]:
        h1, h2, h3 = st.columns(3)
        h1.markdown("**Name**")
        h2.markdown("**ID (mm)**")
        h3.markdown("**Depth (m)**")

        for r in st.session_state.job["well"]["restrictions"]:
            r1, r2, r3 = st.columns(3)
            r1.write(r["name"])
            r2.write(r["id_mm"])
            r3.write(r["depth_m"])

    st.markdown("---")

    # SCHEMATIC
    st.subheader("Well Schematic")
    schematic = st.file_uploader("Upload schematic", type=["png", "jpg", "jpeg", "pdf"])
    if schematic:
        st.session_state.job["well"]["schematic"] = schematic

    if st.session_state.job["well"]["schematic"]:
        if st.session_state.job["well"]["schematic"].type == "application/pdf":
            st.info("PDF uploaded.")
        else:
            st.image(st.session_state.job["well"]["schematic"], use_column_width=True)
