import streamlit as st
import math
import json
import os
from datetime import datetime
import csv
import io

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Well Servicing Calculator", layout="wide")

JOB_DIR = "jobs"
os.makedirs(JOB_DIR, exist_ok=True)

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

# ---------------- STATE INIT ----------------
def init_state():
    st.session_state.setdefault("settings", {"rate_unit": "m/min", "force_unit": "daN"})
    st.session_state.setdefault("active_ct", None)

    st.session_state.setdefault("well", {
        "job_name": "",
        "tvd": "",
        "kop": "",
        "td": "",
        "casing": []
    })

    st.session_state.setdefault("ct_strings", {})

    st.session_state.setdefault("fluid", {
        "base_type": "Fresh Water",
        "base_density": FRESH_WATER_DENSITY,
        "chemicals": []
    })

init_state()

# ---------------- JOB IO ----------------
def save_job(name):
    job = {
        "well": st.session_state.well,
        "ct_strings": st.session_state.ct_strings,
        "fluid": st.session_state.fluid,
        "settings": st.session_state.settings,
        "active_ct": st.session_state.active_ct
    }
    with open(f"{JOB_DIR}/{name}.json", "w") as f:
        json.dump(job, f, indent=2)

def load_job(name):
    with open(f"{JOB_DIR}/{name}.json", "r") as f:
        job = json.load(f)

    st.session_state.well = job.get("well", {})
    st.session_state.ct_strings = job.get("ct_strings", {})
    st.session_state.fluid = job.get("fluid", {})
    st.session_state.settings = job.get("settings", {})
    st.session_state.active_ct = job.get("active_ct")

# ---------------- EXPORT HELPERS ----------------
def generate_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    w = st.session_state.well
    ct_name = st.session_state.active_ct
    ct = st.session_state.ct_strings.get(ct_name, [])

    writer.writerow(["JOB SUMMARY"])
    writer.writerow(["Job Name", w.get("job_name", "")])
    writer.writerow(["Exported", datetime.now().isoformat()])
    writer.writerow([])

    writer.writerow(["Well Info"])
    writer.writerow(["TVD (m)", w.get("tvd", "")])
    writer.writerow(["KOP (m)", w.get("kop", "")])
    writer.writerow(["TD (m)", w.get("td", "")])
    writer.writerow([])

    writer.writerow(["Casing / Liner"])
    writer.writerow(["Type", "From (m)", "To (m)", "ID (mm)"])
    for c in w.get("casing", []):
        writer.writerow([c["type"], c["from"], c["to"], c["id_mm"]])

    writer.writerow([])
    writer.writerow(["CT String", ct_name])
    writer.writerow(["Section", "Length (m)", "OD (mm)", "Wall (mm)"])

    total_length = 0
    for i, sec in enumerate(ct, 1):
        total_length += sec["length"]
        writer.writerow([i, sec["length"], sec["od"], sec["wall"]])

    writer.writerow(["Total Length (m)", total_length])
    writer.writerow([])

    writer.writerow(["Fluids"])
    writer.writerow(["Base Fluid", st.session_state.fluid["base_type"]])
    writer.writerow(["Base Density (kg/m³)", st.session_state.fluid["base_density"]])

    for chem in st.session_state.fluid["chemicals"]:
        writer.writerow(["Chemical", chem["name"], chem["density"], chem["rate"]])

    return output.getvalue()

# ---------------- HEADER ----------------
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

# ---------------- NAV ----------------
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🛢️ Well / Job",
        "🧵 CT String Builder",
        "🧊 Volumes",
        "🧪 Fluids",
        "💾 Jobs",
        "📤 Export",
        "⚙️ Settings"
    ],
    label_visibility="collapsed"
)

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.success("Field-ready calculations with saved jobs.")

# ---------------- FLUIDS ----------------
elif page == "🧪 Fluids":
    st.header("Fluids & Chemicals")

    base_type = st.selectbox(
        "Base Fluid",
        ["Fresh Water", "Produced Water", "Custom"],
        index=["Fresh Water", "Produced Water", "Custom"].index(
            st.session_state.fluid.get("base_type", "Fresh Water")
        )
    )

    if base_type == "Fresh Water":
        base_density = FRESH_WATER_DENSITY
    elif base_type == "Produced Water":
        base_density = PRODUCED_WATER_DENSITY
    else:
        base_density = st.number_input(
            "Custom Density (kg/m³)",
            min_value=800.0,
            value=float(st.session_state.fluid.get("base_density", 1000.0))
        )

    st.session_state.fluid["base_type"] = base_type
    st.session_state.fluid["base_density"] = base_density

    st.subheader("Add Chemical")

    col1, col2, col3 = st.columns(3)
    with col1:
        chem_name = st.text_input("Name")
    with col2:
        chem_density = st.number_input("Density (kg/m³)", min_value=500.0)
    with col3:
        chem_rate = st.number_input("Mix Rate (L/m³)", min_value=0.0)

    if st.button("Add Chemical"):
        if chem_name:
            st.session_state.fluid["chemicals"].append({
                "name": chem_name,
                "density": chem_density,
                "rate": chem_rate
            })

    st.subheader("Current Chemicals")
    for i, c in enumerate(st.session_state.fluid["chemicals"], 1):
        st.write(f"{i}. {c['name']} @ {c['rate']} L/m³ | {c['density']} kg/m³")

    total_rate = sum(c["rate"] for c in st.session_state.fluid["chemicals"])
    blended_density = (
        (base_density * (1000 - total_rate)) +
        sum(c["density"] * c["rate"] for c in st.session_state.fluid["chemicals"])
    ) / 1000

    st.success(f"Blended Density: {blended_density:.1f} kg/m³")

# ---------------- JOBS ----------------
elif page == "💾 Jobs":
    st.header("Job Manager")

    name = st.text_input("Job Name", st.session_state.well.get("job_name", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Job"):
            if name:
                st.session_state.well["job_name"] = name
                save_job(name)
                st.success("Job saved.")
    with col2:
        jobs = [f.replace(".json", "") for f in os.listdir(JOB_DIR)]
        selected = st.selectbox("Load Job", [""] + jobs)
        if st.button("📂 Load Job") and selected:
            load_job(selected)
            st.success("Job loaded.")

# ---------------- EXPORT ----------------
elif page == "📤 Export":
    st.header("Export Job Summary")

    if not st.session_state.active_ct:
        st.warning("Select an active CT string before exporting.")
        st.stop()

    csv_data = generate_csv()

    st.download_button(
        "⬇️ Download CSV",
        csv_data,
        file_name=f"{st.session_state.well.get('job_name','job')}_summary.csv",
        mime="text/csv"
    )

# ---------------- SETTINGS ----------------
elif page == "⚙️ Settings":
    st.header("Settings")
    st.session_state.settings["rate_unit"] = st.selectbox(
        "Rate Unit", ["m/min", "ft/min", "bbl/min"]
    )
    st.session_state.settings["force_unit"] = st.selectbox(
        "Force Unit", ["daN", "lbf"]
    )
