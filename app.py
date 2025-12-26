
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

if calc == "Annular Velocity":
    st.header("Annular Velocity")

    rate = st.number_input("Pump rate", min_value=0.0)
    annular_area = st.number_input("Annular area", min_value=0.0)

    if annular_area > 0:
        velocity = rate / annular_area
        st.success(f"Annular velocity: {velocity:.2f}")

elif calc == "Pipe Capacity":
    st.header("Pipe Capacity")
    st.info("This calculator will be wired to your verified formulas.")

