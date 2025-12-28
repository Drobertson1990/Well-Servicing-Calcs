import streamlit as st
import math
from state import default_job

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# -------------------------------------------------
# JOB STATE (SINGLE SOURCE OF TRUTH)
# -------------------------------------------------
if "job" not in st.session_state:
    st.session_state.job = default_job()

job = st.session_state.job

# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------
st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Home",
        "🧵 CT Strings",
        "🛢️ Well / Job",
        "🌀 Flow & Velocity",
        "🧊 Volumes",
        "🧪 Fluids",
        "📉 Pressure",
        "📋 Job Summary",
        "⚙️ Settings",
    ]
)

# -------------------------------------------------
# HOME
# -------------------------------------------------
if page == "🏠 Home":
    st.title("Well Servicing Calculator")

    st.markdown("""
    **Field-ready engineering tools for:**
    - Coiled Tubing
    - Service Rigs
    - Snubbing

    Built to reduce mistakes, speed up planning,  
    and improve supervisor–engineer alignment.
    """)

# -------------------------------------------------
# CT STRING BUILDER
# -------------------------------------------------
elif page == "🧵 CT Strings":
    st.header("CT String Builder")

    # ---------- CREATE STRING ----------
    st.subheader("Create New CT String")

    new_name = st.text_input("String name")

    if st.button("Create string"):
        if new_name:
            job["ct"]["strings"].append({
                "name": new_name,
                "sections": []
            })
            job["ct"]["active_index"] = len(job["ct"]["strings"]) - 1
        else:
            st.warning("Please enter a string name")

    # ---------- SELECT ACTIVE ----------
    if job["ct"]["strings"]:
        names = [s["name"] for s in job["ct"]["strings"]]

        active_name = st.selectbox(
            "Active CT String",
            names,
            index=job["ct"]["active_index"]
            if job["ct"]["active_index"] is not None else 0
        )

        job["ct"]["active_index"] = names.index(active_name)
        ct = job["ct"]["strings"][job["ct"]["active_index"]]

        st.markdown("---")

        # ---------- ADD SECTION ----------
        st.subheader("Add Section (Whip → Core)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            label = st.text_input("Section label", "Whip")

        with col2:
            length_m = st.number_input(
                "Length (m)",
                min_value=0.0,
                value=None
            )

        with col3:
            od_mm = st.selectbox(
                "OD",
                [25.4, 31.75, 38.1, 44.45, 50.8, 57.15, 73.03],
                format_func=lambda x: f"{x} mm"
            )

        with col4:
            wall_mm = st.number_input(
                "Wall thickness (mm)",
                min_value=0.0,
                value=None
            )

        if st.button("Add section"):
            if length_m and wall_mm:
                ct["sections"].append({
                    "label": label,
                    "length_m": length_m,
                    "od_mm": od_mm,
                    "wall_mm": wall_mm
                })
            else:
                st.warning("Length and wall thickness required")

        # ---------- DISPLAY + TRIM ----------
        if ct["sections"]:
            st.markdown("---")
            st.subheader("Sections (Whip → Core)")

            total_length = 0.0
            total_volume = 0.0

            for i, sec in enumerate(ct["sections"]):
                id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
                id_m = id_mm / 1000
                area = math.pi * (id_m / 2) ** 2
                volume = area * sec["length_m"]

                total_length += sec["length_m"]
                total_volume += volume

                st.write(
                    f"{i+1}. {sec['label']} | "
                    f"{sec['length_m']} m | "
                    f"OD {sec['od_mm']} mm | "
                    f"Wall {sec['wall_mm']} mm | "
                    f"Volume {volume:.3f} m³"
                )

            st.markdown("---")
            st.success(f"Total CT Length: {total_length:.1f} m")
            st.success(f"Total Internal Volume: {total_volume:.3f} m³")

            st.subheader("Trim Whip End")

            trim_m = st.number_input(
                "Trim length (m)",
                min_value=0.0,
                value=None
            )

            if st.button("Trim whip"):
                if trim_m:
                    ct["sections"][0]["length_m"] = max(
                        0,
                        ct["sections"][0]["length_m"] - trim_m
                    )

# -------------------------------------------------
# PLACEHOLDERS (LOCKED STRUCTURE)
# -------------------------------------------------
elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")
    st.info("Coming next — geometry, casing, restrictions, schematic")

elif page == "🌀 Flow & Velocity":
    st.header("Flow & Velocity")
    st.info("Will auto-use CT + well geometry")

elif page == "🧊 Volumes":
    st.header("Volumes")
    st.info("CT displacement, annular, total circulating volume")

elif page == "🧪 Fluids":
    st.header("Fluids")
    st.info("Base fluid, chemicals, blended density")

elif page == "📉 Pressure":
    st.header("Pressure")
    st.info("Hydrostatic first, friction later")

elif page == "📋 Job Summary":
    st.header("Job Summary")
    st.info("Auto-generated overview")

elif page == "⚙️ Settings":
    st.header("Settings")
    st.info("Units, display, preferences")
