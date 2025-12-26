import streamlit as st
import math
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# ==============================
# SESSION STATE
# ==============================
if "jobs" not in st.session_state:
    st.session_state.jobs = {}

# ==============================
# HEADER
# ==============================
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

st.markdown("""
Field-ready calculations for oilfield operations.  
Designed to save time, reduce errors, and standardize job planning.
""")

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("Job / Well")

job_name = st.sidebar.text_input("Job / Well name")

if job_name:
    if job_name not in st.session_state.jobs:
        st.session_state.jobs[job_name] = {}

calc = st.sidebar.selectbox(
    "Choose a calculator",
    [
        "Home",
        "Annular Velocity",
        "CT String Builder",
    ]
)

# ==============================
# HOME
# ==============================
if calc == "Home":
    st.header("Welcome")
    st.write("Select a calculator from the menu.")

# ==============================
# ANNULAR VELOCITY
# ==============================
elif calc == "Annular Velocity":
    st.header("Annular Velocity")

    if not job_name or not st.session_state.jobs[job_name]:
        st.warning("Create a job and CT string first.")
    else:
        string_name = st.selectbox(
            "Select CT String",
            list(st.session_state.jobs[job_name].keys())
        )

        sections = st.session_state.jobs[job_name][string_name]["sections"]

        min_id_mm = min(
            sec["od_mm"] - 2 * sec["wall_mm"] for sec in sections
        )

        st.info(f"Using minimum CT ID: {min_id_mm:.2f} mm")

        outer_id_mm = st.number_input("Casing / Tubing ID (mm)", min_value=0.0)

        rate_unit = st.selectbox("Pump rate unit", ["m³/min", "L/min", "bbl/min"])
        rate = st.number_input(f"Pump rate ({rate_unit})", min_value=0.0)

        if outer_id_mm > min_id_mm:
            outer_area = math.pi * (outer_id_mm / 2000) ** 2
            inner_area = math.pi * (min_id_mm / 2000) ** 2
            annular_area = outer_area - inner_area

            if rate_unit == "L/min":
                rate_m3 = rate / 1000
            elif rate_unit == "bbl/min":
                rate_m3 = rate * 0.158987
            else:
                rate_m3 = rate

            velocity = rate_m3 / annular_area
            st.success(f"Annular velocity: {velocity:.2f} m/min")

# ==============================
# CT STRING BUILDER
# ==============================
elif calc == "CT String Builder":
    st.header("CT String Builder")

    if not job_name:
        st.warning("Enter a Job / Well name in the sidebar.")
    else:
        string_name = st.text_input("CT String name")

        max_pull = st.number_input(
            "Max Pull (kN or daN)", min_value=0.0
        )
        max_cycle = st.number_input(
            "Max Cycling Pressure (% of yield)", min_value=0.0
        )

        if string_name and string_name not in st.session_state.jobs[job_name]:
            st.session_state.jobs[job_name][string_name] = {
                "sections": [],
                "max_pull": max_pull,
                "max_cycle": max_cycle,
            }

        # -------- ADD SECTION --------
        st.subheader("Add Section (Whip → Core)")
        col1, col2, col3 = st.columns(3)

        with col1:
            length_m = st.number_input("Length (m)", min_value=0.0)
        with col2:
            od_mm = st.number_input("OD (mm)", min_value=0.0)
        with col3:
            wall_mm = st.number_input("Wall (mm)", min_value=0.0)

        if st.button("Add section"):
            st.session_state.jobs[job_name][string_name]["sections"].append(
                {
                    "length_m": length_m,
                    "od_mm": od_mm,
                    "wall_mm": wall_mm,
                }
            )

        # -------- DISPLAY & EDIT --------
        if string_name in st.session_state.jobs[job_name]:
            sections = st.session_state.jobs[job_name][string_name]["sections"]

            st.markdown("---")
            st.markdown("**Whip End → Core**")

            running_depth = 0.0
            total_length = 0.0
            total_volume = 0.0

            for i, sec in enumerate(sections):
                id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
                area = math.pi * (id_mm / 2000) ** 2
                volume = area * sec["length_m"]

                start = running_depth
                end = running_depth + sec["length_m"]
                running_depth = end

                total_length += sec["length_m"]
                total_volume += volume

                colA, colB, colC = st.columns([6, 1, 1])

                with colA:
                    st.write(
                        f"{start:.0f}–{end:.0f} m | "
                        f"OD {sec['od_mm']} mm | "
                        f"Wall {sec['wall_mm']} mm"
                    )

                with colB:
                    if st.button("↑", key=f"up_{i}") and i > 0:
                        sections[i - 1], sections[i] = sections[i], sections[i - 1]

                with colC:
                    if st.button("↓", key=f"dn_{i}") and i < len(sections) - 1:
                        sections[i + 1], sections[i] = sections[i], sections[i + 1]

            st.success(f"Total length: {total_length:.1f} m")
            st.success(f"Total volume: {total_volume:.3f} m³")

            # -------- PDF EXPORT --------
            if st.button("Export CT String PDF"):
                fd, path = tempfile.mkstemp(".pdf")
                c = canvas.Canvas(path, pagesize=letter)

                c.drawString(50, 750, f"Job: {job_name}")
                c.drawString(50, 735, f"CT String: {string_name}")
                c.drawString(50, 720, f"Max Pull: {max_pull}")
                c.drawString(50, 705, f"Max Cycling %: {max_cycle}")

                y = 670
                for sec in sections:
                    c.drawString(
                        50, y,
                        f"{sec['length_m']} m | OD {sec['od_mm']} | Wall {sec['wall_mm']}"
                    )
                    y -= 15

                c.save()

                with open(path, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f,
                        file_name=f"{string_name}.pdf"
                    )

                os.remove(path)

