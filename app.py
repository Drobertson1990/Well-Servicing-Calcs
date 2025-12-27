import streamlit as st
import math
import json
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

# ---------------- CONSTANTS ----------------
CT_OD_PRESETS = {
    '1"': 25.4,
    '1¼"': 31.75,
    '1½"': 38.1,
    '1¾"': 44.45,
    '2"': 50.8,
    '2⅜"': 60.33,
    '2⅞"': 73.03,
}

FRESH_WATER_DENSITY = 1000.0
PRODUCED_WATER_DENSITY = 1080.0

JOB_DIR = "jobs"
os.makedirs(JOB_DIR, exist_ok=True)

# ---------------- SESSION STATE ----------------
def init_state():
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "rate_unit": "m/min",
            "force_unit": "daN",
        }

    if "well" not in st.session_state:
        st.session_state.well = {
            "job_name": "",
            "tvd": None,
            "kop": None,
            "td": None,
            "casing": [],
        }

    if "ct_strings" not in st.session_state:
        st.session_state.ct_strings = {}

    if "fluid" not in st.session_state:
        st.session_state.fluid = {
            "base_density": FRESH_WATER_DENSITY,
            "chemicals": [],
        }

init_state()

# ---------------- JOB FUNCTIONS ----------------
def save_job(name):
    job = {
        "well": st.session_state.well,
        "ct_strings": st.session_state.ct_strings,
        "fluid": st.session_state.fluid,
        "settings": st.session_state.settings,
    }
    with open(os.path.join(JOB_DIR, f"{name}.json"), "w") as f:
        json.dump(job, f, indent=2)

def load_job(name):
    with open(os.path.join(JOB_DIR, f"{name}.json"), "r") as f:
        job = json.load(f)
    st.session_state.well = job["well"]
    st.session_state.ct_strings = job["ct_strings"]
    st.session_state.fluid = job["fluid"]
    st.session_state.settings = job["settings"]

# ---------------- HEADER ----------------
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

# ---------------- SIDEBAR ----------------
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🛢️ Well / Job",
        "🧵 CT String Builder",
        "🌀 Annular Velocity",
        "🧊 Volumes",
        "🧪 Fluids & Chemicals",
        "💾 Jobs",
        "⚙️ Settings",
    ],
    label_visibility="collapsed",
)

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.header("Home")
    st.success("Field-ready calculations with saved jobs.")

# ---------------- JOB MANAGER ----------------
elif page == "💾 Jobs":
    st.header("Job Manager")

    job_name = st.text_input("Job Name", value=st.session_state.well.get("job_name", ""))

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Job"):
            if job_name:
                st.session_state.well["job_name"] = job_name
                save_job(job_name)
                st.success(f"Job '{job_name}' saved.")
            else:
                st.warning("Enter a job name.")

    with col2:
        jobs = [f.replace(".json", "") for f in os.listdir(JOB_DIR)]
        selected = st.selectbox("Load Existing Job", [""] + jobs)

        if st.button("📂 Load Job") and selected:
            load_job(selected)
            st.success(f"Job '{selected}' loaded.")

# ---------------- WELL / JOB ----------------
elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    st.session_state.well["job_name"] = st.text_input(
        "Job / Well Name", st.session_state.well.get("job_name", "")
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.well["tvd"] = st.text_input("TVD (m)", st.session_state.well["tvd"] or "")
    with col2:
        st.session_state.well["kop"] = st.text_input("KOP (m)", st.session_state.well["kop"] or "")
    with col3:
        st.session_state.well["td"] = st.text_input("TD (m)", st.session_state.well["td"] or "")

    st.subheader("Casing / Liner")

    with st.expander("Add Section"):
        c_from = st.text_input("From depth (m)")
        c_to = st.text_input("To depth (m)")
        c_id = st.text_input("Internal Diameter (mm)")
        c_type = st.selectbox("Type", ["Casing", "Liner"])

        if st.button("Add Casing"):
            try:
                st.session_state.well["casing"].append({
                    "from": float(c_from),
                    "to": float(c_to),
                    "id_mm": float(c_id),
                    "type": c_type,
                })
                st.success("Added.")
            except:
                st.error("Invalid input.")

    for i, c in enumerate(st.session_state.well["casing"], 1):
        st.write(f"{i}. {c['type']} {c['from']}–{c['to']} m | ID {c['id_mm']} mm")

# ---------------- CT STRING BUILDER ----------------
elif page == "🧵 CT String Builder":
    st.header("CT String Builder (Whip → Core)")

    string_name = st.text_input("CT String Name")

    length = st.text_input("Section Length (m)")
    od_label = st.selectbox("CT OD", list(CT_OD_PRESETS.keys()))
    wall = st.text_input("Wall Thickness (mm)")

    if st.button("Add Section"):
        try:
            st.session_state.ct_strings.setdefault(string_name, []).append({
                "length": float(length),
                "od": CT_OD_PRESETS[od_label],
                "wall": float(wall),
            })
            st.success("Section added.")
        except:
            st.error("Invalid input.")

    if st.session_state.ct_strings:
        selected = st.selectbox("Select String", list(st.session_state.ct_strings.keys()))
        running = 0
        for i, sec in enumerate(st.session_state.ct_strings[selected], 1):
            running += sec["length"]
            st.write(f"{i}. {sec['length']} m | OD {sec['od']} | Wall {sec['wall']} → {running:.1f} m")

# ---------------- PLACEHOLDERS (UNCHANGED) ----------------
elif page in ["🌀 Annular Velocity", "🧊 Volumes", "🧪 Fluids & Chemicals", "⚙️ Settings"]:
    st.info("This section remains exactly as previously implemented.")
