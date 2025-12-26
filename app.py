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
if "ct_strings" not in st.session_state:
    st.session_state.ct_strings = {}

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
st.sidebar.header("Calculators")

st.sidebar.subheader("Well Schematic")
schematic = st.sidebar.file_uploader(
    "Upload well schematic",
    type=["png", "jpg", "jpeg", "pdf"]
)

calc = st.sidebar.selectbox(
    "Choose a calculator",
    [
        "Home",
        "Annular Velocity",
        "Pipe Capacity",
        "CT String Builder",
        "Fluid Volumes",
    ]
)

# ==============================
# HOME
# ==============================
if calc == "Home":
    st.header("Welcome")
    st.write("Select a calculator from the left menu.")

# ==============================
# ANNULAR VELOCITY
# ==============================
elif calc == "Annular Velocity":
    st.header("Annular Velocity")

    st.subheader("Pipe Information")
    outer_id_mm = st.number_input("Outer pipe ID (mm)", min_value=0.0)
    inner_od_mm = st.number_input("Inner pipe OD (mm)", min_value=0.0)

    st.subheader("Pump Rate")
    rate_unit = st.selectbox(
        "Pump rate unit",
        ["m³/min", "L/min", "bbl/min"]
    )

    rate = st.number_input(
        f"Pump rate ({rate_unit})",
        min_value=0.0
    )

    if outer_id_mm > inner_od_mm > 0:
        outer_id_m = outer_id_mm / 1000
        inner_od_m = inner_od_mm / 1000

        annular_area = (
            math.pi * (outer_id_m / 2) ** 2
            - math.pi * (inner_od_m / 2) ** 2
        )

        if rate_unit == "L/min":
            rate_m3 = rate / 1000
        elif rate_unit == "bbl/min":
            rate_m3 = rate * 0.158987
        else:
            rate_m3 = rate

        velocity = rate_m3 / annular_area
        st.success(f"Annular velocity: {velocity:.2f} m/min")
    else:
        st.warning("Outer ID must be larger than inner OD.")

# ==============================
# PIPE CAPACITY (PLACEHOLDER)
# ==============================
elif calc == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("Calculator coming soon.")

# ==============================
# CT STRING BUILDER
# ==============================
elif calc == "CT String Builder":
    st.header("CT String Builder")

    st.markdown("""
Build and edit coiled tubing strings **from Whip End to Core**.  
Supports multiple wall thickness sections and field adjustments.
""")

    # --------------------------
    # STRING NAME
    # --------------------------
    string_name = st.text_input("CT String name")

    # --------------------------
    # ADD SECTION
    # --------------------------
    st.subheader("Add Section (Whip → Core)")

    col1, col2, col3 = st.columns(3)

    with col1:
        length_m = st.number_input("Section length (m)", min_value=0.0, key="len")

    with col2:
        od_mm = st.number_input("OD (mm)", min_value=0.0, key="od")

    with col3:
        wall_mm = st.number_input("Wall thickness (mm)", min_value=0.0, key="wall")

    if st.button("Add section"):
        if string_name and length_m > 0 and od_mm > 0 and wall_mm > 0:
            if string_name not in st.session_state.ct_strings:
                st.session_state.ct_strings[string_name] = []

            st.session_state.ct_strings[string_name].append(
                {
                    "length_m": length_m,
                    "od_mm": od_mm,
                    "wall_mm": wall_mm,
                }
            )
        else:
            st.warning("Please fill in all fields and name the string.")

    # --------------------------
    # EDIT EXISTING STRINGS
    # --------------------------
    if st.session_state.ct_strings:
        st.markdown("---")
        st.subheader("Saved CT Strings")

        selected_string = st.selectbox(
            "Select a CT string",
            list(st.session_state.ct_strings.keys())
        )

        sections = st.session_state.ct_strings[selected_string]

        # --------------------------
        # TRIM WHIP END (NO RERUN)
        # --------------------------
        st.markdown("### Trim Whip End")

        trim_m = st.number_input(
            "Remove length from whip end (m)",
            min_value=0.0,
            key="trim"
        )

        if st.button("Apply trim"):
            remaining = trim_m
            new_sections = []

            for sec in sections:
                if remaining <= 0:
                    new_sections.append(sec)
                elif sec["length_m"] > remaining:
                    sec["length_m"] -= remaining
                    new_sections.append(sec)
                    remaining = 0
                else:
                    remaining -= sec["length_m"]

            st.session_state.ct_strings[selected_string] = new_sections

        # --------------------------
        # DISPLAY STRING
        # --------------------------
        st.markdown("---")
        st.markdown("**String orientation: Whip End → Core**")

        total_length = 0.0
        total_volume = 0.0
        running_depth = 0.0

        for i, sec in enumerate(st.session_state.ct_strings[selected_string], start=1):
            id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
            id_m = id_mm / 1000

            area = math.pi * (id_m / 2) ** 2
            volume = area * sec["length_m"]

            start_depth = running_depth
            end_depth = running_depth + sec["length_m"]
            running_depth = end_depth

            total_length += sec["length_m"]
            total_volume += volume

            col_a, col_b = st.columns([6, 1])

            with col_a:
                st.write(
                    f"Section {i}: {start_depth:.0f}–{end_depth:.0f} m | "
                    f"OD {sec['od_mm']} mm | Wall {sec['wall_mm']} mm | "
                    f"Volume {volume:.3f} m³"
                )

            with col_b:
                if st.button("❌", key=f"delete_{i}"):
                    st.session_state.ct_strings[selected_string].pop(i - 1)

        st.markdown("---")
        st.success(f"Total length: {total_length:.1f} m")
        st.success(f"Total internal volume: {total_volume:.3f} m³")

# ==============================
# FLUID VOLUMES (PLACEHOLDER)
# ==============================
elif calc == "Fluid Volumes":
    st.header("Fluid Volumes")
    st.info("Calculator coming soon.")

# ==============================
# SCHEMATIC DISPLAY
# ==============================
if schematic:
    st.markdown("---")
    st.subheader("Well Schematic")

    if schematic.type == "application/pdf":
        st.info("PDF uploaded. Display support coming soon.")
    else:
        st.image(schematic, use_column_width=True)
