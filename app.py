
import streamlit as st

st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

st.markdown("""
Select a calculator from the menu on the left.
This tool is designed for **field-ready calculations**:
- Fast
- Repeatable
- Error-resistant
""")

st.sidebar.header("Calculators")

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

if calc == "Home":
    st.header("Welcome")
    st.write("Select a calculator from the left menu.")

elif calc == "Annular Velocity":
    st.header("Annular Velocity")

    rate_unit = st.selectbox(
        "Pump rate unit",
        ["m³/min", "L/min", "bbl/min"]
    )

    rate = st.number_input(
        f"Pump rate ({rate_unit})",
        min_value=0.0
    )

    annular_area = st.number_input(
        "Annular area (m²)",
        min_value=0.0
    )

    if annular_area > 0:
        if rate_unit == "L/min":
            rate_m3 = rate / 1000
        elif rate_unit == "bbl/min":
            rate_m3 = rate * 0.158987
        else:
            rate_m3 = rate

        velocity = rate_m3 / annular_area
        st.success(f"Annular velocity: {velocity:.2f} m/min")

elif calc == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("Calculator coming soon.")

elif calc == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("This calculator will be wired to your verified formulas.")

