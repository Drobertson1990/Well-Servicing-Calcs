import streamlit as st
import math

# ===============================
# Session State Initialization
# ===============================
if "ct_strings" not in st.session_state:
    st.session_state.ct_strings = {}

# ===============================
# Page Config
# ===============================
st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# ===============================
# Header
# ===============================
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

st.markdown("""
Field-ready calculations for oilfield operations.

Designed to:
- Save time
- Reduce errors
- Standardize job planning
""")

# ===============================
# Sidebar
# ===============================
st.sidebar.header("Navigation")

st.sidebar.subheader("Well Schematic")
schematic = st.sidebar.file_uploader(
    "Upload well schematic",
    type=["png", "jpg", "jpeg", "pdf"]
)

calc = st.sidebar.selectbox(
    "Choose a tool",
    [
        "Home",
        "Annular Velocity",
        "CT String Builder",
        "Pipe Capacity (coming soon)",
        "Fluid Volumes (coming soon)",
    ]
)

# ===============================
# Main Content
# ===============================

# -------- HOME --------
if calc == "Home":
    st.header("Welcome")
    st.write(
        "Select a tool from the left menu. "
        "This application is built for daily field and office calculations."
    )

# -------- ANNULAR VELOCITY --------
elif calc == "Annular Velocity":
    st.header("Annular Velocity")

    st.subheader("Pipe Geometry")

    outer_id_mm = st.number_input(
        "Outer pipe ID (mm)",
        min_value=0.0
    )

    inner_od_mm = st.number_input(
        "Inner pipe OD (mm)",
        min_value=0.0
    )

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
        # Convert mm → m
        outer_id_m = outer_id_mm / 1000
        inner_od_m = inner_od_mm / 1000

        outer_area = math.pi * (outer_id_m / 2) ** 2
        inner_area = math.pi * (inner_od_m / 2) ** 2
        annular_area = outer_area - inner_area

        # Convert rate to m³/min
        if rate_unit == "L/min":
            rate_m3 = rate / 1000
        elif rate_unit == "bbl/min":
            rate_m3 = rate * 0.158987
        else:
            rate_m3 = rate

        velocity = rate_m3 / annular_area

        st.success(f"Annular velocity: {velocity:.2f} m/min")
        st.caption(f"Annular area: {annular_area:.4f} m²")
    else:
        st.warning("Outer pipe ID must be larger than inner pipe OD.")

# -------- CT STRING BUILDER --------
elif calc == "CT String Builder":
    st.header("CT String Builder")

    st.markdown(
        "Build and save coiled tubing strings with multiple wall thickness sections."
    )

    string_name = st.text_input("CT String name")

    st.subheader("Add Section")

    col1, col2, col3 = st.columns(3)

    with col1:
        length_m = st.number_input(
            "Section length (m)",
            min_value=0.0
        )

    with col2:
        od_mm = st.number_input(
            "OD (mm)",
            min_value=0.0
        )

    with col3:
        wall_mm = st.number_input(
            "Wall thickness (mm)",
            min_value=0.0
        )

    if st.button("Add section"):
        if string_name and length_m > 0 and od_mm > 0 and wall_mm > 0:
            if wall_mm * 2 >= od_mm:
                st.error("Wall thickness too large for given OD.")
            else:
                section = {
                    "length_m": length_m,
                    "od_mm": od_mm,
                    "wall_mm": wall_mm
                }

                if string_name not in st.session_state.ct_strings:
                    st.session_state.ct_strings[string_name] = []

                st.session_state.ct_strings[string_name].append(section)
        else:
            st.warning("Enter all values and provide a string name.")

    # ----- Display Saved Strings -----
    if st.session_state.ct_strings:
        st.markdown("---")
        st.subheader("Saved CT Strings")

        selected_string = st.selectbox(
            "Select CT string",
            list(st.session_state.ct_strings.keys())
        )

        sections = st.session_state.ct_strings[selected_string]

        total_length = 0.0
        total_volume = 0.0

        for i, sec in enumerate(sections, start=1):
            id_mm = sec["od_mm"] - 2 * sec["wall_mm"]
            id_m = id_mm / 1000

            area = math.pi * (id_m / 2) ** 2
            volume = area * sec["length_m"]

            total_length += sec["length_m"]
            total_volume += volume

            st.write(
                f"Section {i}: "
                f"{sec['length_m']} m | "
                f"OD {sec['od_mm']} mm | "
                f"Wall {sec['wall_mm']} mm | "
                f"Volume {volume:.3f} m³"
            )

        st.markdown("---")
        st.success(f"Total length: {total_length:.1f} m")
        st.success(f"Total internal volume: {total_volume:.3f} m³")

# -------- PLACEHOLDERS --------
elif calc == "Pipe Capacity (coming soon)":
    st.header("Pipe Capacity")
    st.info("Calculator coming soon.")

elif calc == "Fluid Volumes (coming soon)":
    st.header("Fluid Volumes")
    st.info("Calculator coming soon.")

# ===============================
# Well Schematic Display
# ===============================
if schematic:
    st.markdown("---")
    st.subheader("Well Schematic")

    if schematic.type == "application/pdf":
        st.info("PDF uploaded. Display support coming soon.")
    else:
        st.image(schematic, use_column_width=True)
