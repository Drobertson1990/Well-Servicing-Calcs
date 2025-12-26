import streamlit as st
import math

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

if "units" not in st.session_state:
    st.session_state.units = {
        "force": "kN",
        "rate": "m/min"
    }

# ==============================
# HEADER
# ==============================
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

# ==============================
# SIDEBAR – JOB & SETTINGS
# ==============================
st.sidebar.header("Job / Well")
job_name = st.sidebar.text_input("Job / Well name")

if job_name and job_name not in st.session_state.jobs:
    st.session_state.jobs[job_name] = {}

st.sidebar.markdown("---")
st.sidebar.header("Units")

st.session_state.units["force"] = st.sidebar.selectbox(
    "Pull force unit",
    ["kN", "daN", "lbs"]
)

st.session_state.units["rate"] = st.sidebar.selectbox(
    "Rate unit",
    ["m/min", "ft/min"]
)

calc = st.sidebar.selectbox(
    "Select tool",
    [
        "Home",
        "CT String Builder",
        "Annular Velocity",
        "Engineering Summary",
        "IRP Quick-Look (Canada)",
    ]
)

# ==============================
# HOME
# ==============================
if calc == "Home":
    st.header("Welcome")
    st.write("Select a tool from the sidebar.")

# ==============================
# CT STRING BUILDER
# ==============================
elif calc == "CT String Builder":

    if not job_name:
        st.warning("Enter a Job / Well name.")
    else:
        st.header("CT String Builder")

        string_name = st.text_input("CT String name")

        max_pull = st.number_input(
            f"Max Pull ({st.session_state.units['force']})",
            min_value=0.0
        )

        max_cycle = st.number_input(
            "Max Cycling Pressure (% yield)",
            min_value=0.0,
            max_value=100.0
        )

        if string_name and string_name not in st.session_state.jobs[job_name]:
            st.session_state.jobs[job_name][string_name] = {
                "sections": [],
                "max_pull": max_pull,
                "max_cycle": max_cycle
            }

        st.subheader("Add Section (Whip → Core)")
        col1, col2, col3 = st.columns(3)

        with col1:
            length_m = st.number_input("Length (m)", min_value=0.0)
        with col2:
            od_mm = st.number_input("OD (mm)", min_value=0.0)
        with col3:
            wall_mm = st.number_input("Wall (mm)", min_value=0.0)

        if st.button("Add section") and string_name:
            st.session_state.jobs[job_name][string_name]["sections"].append(
                {
                    "length_m": length_m,
                    "od_mm": od_mm,
                    "wall_mm": wall_mm
                }
            )

        if string_name in st.session_state.jobs[job_name]:
            sections = st.session_state.jobs[job_name][string_name]["sections"]

            st.markdown("### Whip End → Core")

            depth = 0.0
            total_length = 0.0
            total_volume = 0.0

            for sec in sections:
                id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
                area = math.pi * (id_mm / 2000) ** 2
                volume = area * sec["length_m"]

                start = depth
                end = depth + sec["length_m"]
                depth = end

                total_length += sec["length_m"]
                total_volume += volume

                st.write(
                    f"{start:.0f}–{end:.0f} m | "
                    f"OD {sec['od_mm']} mm | Wall {sec['wall_mm']} mm"
                )

            st.success(f"Total Length: {total_length:.1f} m")
            st.success(f"Total Volume: {total_volume:.3f} m³")

# ==============================
# ANNULAR VELOCITY
# ==============================
elif calc == "Annular Velocity":

    st.header("Annular Velocity")

    if not job_name or not st.session_state.jobs[job_name]:
        st.warning("Create a CT string first.")
    else:
        string = st.selectbox(
            "Select CT string",
            list(st.session_state.jobs[job_name].keys())
        )

        sections = st.session_state.jobs[job_name][string]["sections"]
        min_id = min(sec["od_mm"] - 2 * sec["wall_mm"] for sec in sections)

        casing_id = st.number_input("Casing / Tubing ID (mm)", min_value=0.0)
        rate = st.number_input("Pump rate (m³/min)", min_value=0.0)

        if casing_id > min_id:
            ann_area = (
                math.pi * (casing_id / 2000) ** 2
                - math.pi * (min_id / 2000) ** 2
            )
            velocity = rate / ann_area
            st.success(f"Annular Velocity: {velocity:.2f} m/min")

# ==============================
# ENGINEERING SUMMARY
# ==============================
elif calc == "Engineering Summary":

    if not job_name:
        st.warning("Select a job.")
    else:
        st.header("Engineering Summary")

        for name, data in st.session_state.jobs[job_name].items():
            st.subheader(name)
            st.write(f"Max Pull: {data['max_pull']} {st.session_state.units['force']}")
            st.write(f"Max Cycling: {data['max_cycle']} %")

            total_len = sum(sec["length_m"] for sec in data["sections"])
            st.write(f"Total Length: {total_len:.1f} m")

# ==============================
# IRP QUICK LOOK
# ==============================
elif calc == "IRP Quick-Look (Canada)":

    st.header("Canadian IRP Quick-Look")
    st.info("Reference only — not a substitute for regulations.")

    st.markdown("""
### Common CT / Snubbing Considerations
- BOP pressure testing required before operations
- Verified pipe specs required on location
- Pressure control equipment must meet MAWP
- Emergency procedures posted and briefed

### Pressure Testing
- Typically 1.25–1.5 × working pressure
- Document all tests

### Personnel
- Competent operator requirements
- Supervisor on site
""")
