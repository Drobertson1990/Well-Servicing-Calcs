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
        "active_ct": None
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

STEEL_DENSITY = 7850  # kg/m3

# =========================
# HELPER FUNCTIONS
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
        area = math.pi * ((od_m/2)**2 - (id_m/2)**2)
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
st.subheader("Phase 1 – CT String Builder (Locked Foundation)")

st.markdown(
    """
This phase establishes the **core CT string engine**.
All downstream calculations will reference this data.
"""
)

# =========================
# SIDEBAR NAV
# =========================
st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "🧵 CT Strings"]
)

# =========================
# HOME
# =========================
if page == "🏠 Home":
    st.header("Home")
    st.write(
        """
        This application is built around **job-centric data**.
        
        Phase 1 focuses on:
        - Building
        - Editing
        - Selecting
        coiled tubing strings.
        """
    )

    if st.session_state.job["active_ct"]:
        st.success(f"Active CT String: {st.session_state.job['active_ct']}")
    else:
        st.warning("No active CT string selected.")

# =========================
# CT STRING BUILDER
# =========================
if page == "🧵 CT Strings":
    st.header("CT String Builder")

    # -------------------------
    # CREATE / SELECT STRING
    # -------------------------
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
            else:
                st.warning("Enter a string name.")

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

    # -------------------------
    # ADD SECTION
    # -------------------------
    if st.session_state.job["active_ct"]:
        st.markdown("---")
        st.subheader("Add Section (Whip → Core)")

        c1, c2, c3 = st.columns(3)

        with c1:
            length_m = st.number_input("Length (m)", min_value=0.0, step=1.0)

        with c2:
            od_label = st.selectbox("OD", list(CT_OD_OPTIONS.keys()))
            od_mm = CT_OD_OPTIONS[od_label]

        with c3:
            wall_mm = st.number_input("Wall thickness (mm)", min_value=0.0, step=0.01)

        if st.button("Add Section"):
            if length_m > 0 and wall_mm > 0:
                st.session_state.job["ct_strings"][st.session_state.job["active_ct"]]["sections"].append(
                    {
                        "length_m": length_m,
                        "od_mm": od_mm,
                        "wall_mm": wall_mm
                    }
                )
            else:
                st.warning("All values must be greater than zero.")

        # -------------------------
        # EDIT / VIEW SECTIONS
        # -------------------------
        sections = st.session_state.job["ct_strings"][st.session_state.job["active_ct"]]["sections"]

        if sections:
            st.markdown("---")
            st.subheader("CT Sections (Whip → Core)")

            for i, s in enumerate(sections):
                st.write(
                    f"Section {i+1}: "
                    f"{s['length_m']} m | "
                    f"OD {s['od_mm']} mm | "
                    f"Wall {s['wall_mm']} mm"
                )

            # -------------------------
            # TRIM WHIP END
            # -------------------------
            st.markdown("---")
            st.subheader("Trim Whip End")

            trim_len = st.number_input("Trim length (m)", min_value=0.0, step=1.0)

            if st.button("Trim"):
                if trim_len > 0:
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

            # -------------------------
            # CALCULATED OUTPUTS
            # -------------------------
            st.markdown("---")
            st.subheader("Calculated Properties")

            total_len = calc_total_length(sections)
            int_vol = calc_internal_volume(sections)
            disp = calc_displacement(sections)

            st.metric("Total Length (m)", f"{total_len:.1f}")
            st.metric("Internal Volume (m³)", f"{int_vol:.3f}")
            st.metric("Displacement (m³)", f"{disp:.3f}")

            st.info("Ratings shown are placeholders (Phase 2 refinement).")

        else:
            st.info("No sections added yet.")
