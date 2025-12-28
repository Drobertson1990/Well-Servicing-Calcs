import streamlit as st
import math
from state import default_job

st.set_page_config(
    page_title="Well Servicing Calculator",
    layout="wide"
)

# ----------------- JOB STATE -----------------
if "job" not in st.session_state:
    st.session_state.job = default_job()

job = st.session_state.job
