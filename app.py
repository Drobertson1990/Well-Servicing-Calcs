import streamlit as st
import math

st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# ---------- HEADER ----------
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

st.markdown("""
Field-ready calculations for oilfield operations.
Designed to save time, reduce errors, and standardize job planning.
""")

# ---------- SIDEBAR ----------
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
        "CT String Builder (coming soon)",
        "Fluid Volumes",
    ]
)

# ---------- MAIN CONTENT ----------
if calc == "Home":
    st.header("Welcome")
    st.write("Select a calculator from the left menu.")

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
        # Convert mm → m
        outer_id_m = outer_id_mm / 1000
        inner_od_m = inner_od_mm / 1000

        outer_area = math.pi * (outer_id_m / 2) ** 2
        inner_area = math.pi * (inner_od_m / 2) ** 2
        annular_area = outer_area - inner_area

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

elif calc == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("Calculator coming soon.")

elif calc == "CT String Builder (coming soon)":
    st.header("CT String Builder")
    st.info("This will allow saved CT strings with multiple wall thickness sections.")

elif calc == "Fluid Volumes":
    st.header("Fluid Volumes")
    st.info("Calculator coming soon.")

# ---------- SCHEMATIC DISPLAY ----------
if schematic:
    st.markdown("---")
    st.subheader("Well Schematic")

    if schematic.type == "application/pdf":
        st.info("PDF uploaded. Display support coming soon.")
    else:
        st.image(schematic, use_column_width=True)
