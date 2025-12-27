import streamlit as st
import math
import json
import os
from datetime import datetime
import csv
import io

# ================== CONFIG ==================
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

# ================== STATE INIT ==================
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

# ================== JOB IO ==================
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

# ================== HEADER ==================
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

# ================== NAV ==================
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🛢️ Well / Job",
        "🧵 CT String Builder",
        "🌀 Annular Velocity",
        "🧊 Volumes",
        "🧪 Fluids",
        "💾 Jobs",
        "📤 Export",
        "⚙️ Settings"
    ],
    label_visibility="collapsed"
)

# ================== HOME ==================
if page == "🏠 Home":
    st.success("All systems loaded. Geometry-driven calculations ready.")

# ================== WELL / JOB ==================
elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    st.session_state.well["job_name"] = st.text_input(
        "Job Name", st.session_state.well.get("job_name", "")
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.well["tvd"] = st.text_input("TVD (m)", st.session_state.well.get("tvd", ""))
    with col2:
        st.session_state.well["kop"] = st.text_input("KOP (m)", st.session_state.well.get("kop", ""))
    with col3:
        st.session_state.well["td"] = st.text_input("TD (m)", st.session_state.well.get("td", ""))

    st.subheader("Casing / Liner")

    with st.expander("Add Section"):
        c_from = st.text_input("From (m)")
        c_to = st.text_input("To (m)")
        c_id = st.text_input("ID (mm)")
        c_type = st.selectbox("Type", ["Casing", "Liner"])

        if st.button("Add Casing"):
            try:
                st.session_state.well["casing"].append({
                    "from": float(c_from),
                    "to": float(c_to),
                    "id_mm": float(c_id),
                    "type": c_type
                })
                st.success("Section added.")
            except:
                st.error("Invalid casing input.")

    for i, c in enumerate(st.session_state.well["casing"], 1):
        st.write(f"{i}. {c['type']} {c['from']}–{c['to']} m | ID {c['id_mm']} mm")

# ================== CT STRING BUILDER ==================
elif page == "🧵 CT String Builder":
    st.header("CT String Builder (Whip → Core)")

    name = st.text_input("CT String Name")

    col1, col2, col3 = st.columns(3)
    with col1:
        length = st.text_input("Section Length (m)")
    with col2:
        od_label = st.selectbox("OD", list(CT_OD_PRESETS.keys()))
    with col3:
        wall = st.text_input("Wall (mm)")

    if st.button("Add Section"):
        try:
            st.session_state.ct_strings.setdefault(name, []).append({
                "length": float(length),
                "od": CT_OD_PRESETS[od_label],
                "wall": float(wall)
            })
            st.success("Section added.")
        except:
            st.error("Invalid section data.")

    if st.session_state.ct_strings:
        st.session_state.active_ct = st.selectbox(
            "Active CT String",
            list(st.session_state.ct_strings.keys()),
            index=0
        )

        running = 0
        for i, sec in enumerate(st.session_state.ct_strings[st.session_state.active_ct], 1):
            running += sec["length"]
            st.write(f"{i}. {sec['length']} m | OD {sec['od']} | Wall {sec['wall']} → {running:.1f} m")

# ================== ANNULAR VELOCITY ==================
elif page == "🌀 Annular Velocity":
    st.header("Annular Velocity")

    if not st.session_state.active_ct or not st.session_state.well["casing"]:
        st.warning("Define casing and select an active CT string first.")
        st.stop()

    depth = st.text_input("Depth (m)")
    rate = st.text_input("Pump Rate (m³/min)")

    try:
        depth = float(depth)
        rate = float(rate)
    except:
        st.stop()

    casing = next(
        (c for c in st.session_state.well["casing"]
         if c["from"] <= depth <= c["to"]), None
    )

    if not casing:
        st.error("No casing at this depth.")
        st.stop()

    remaining = depth
    ct_od = None

    for sec in st.session_state.ct_strings[st.session_state.active_ct]:
        if remaining <= sec["length"]:
            ct_od = sec["od"]
            break
        remaining -= sec["length"]

    ann_area = (
        math.pi * ((casing["id_mm"] / 2000) ** 2) -
        math.pi * ((ct_od / 2000) ** 2)
    )

    velocity = rate / ann_area
    st.success(f"Annular Velocity: {velocity:.2f} m/min")

# ================== VOLUMES ==================
elif page == "🧊 Volumes":
    st.header("Volumes")

    if not st.session_state.active_ct:
        st.warning("Select an active CT string.")
        st.stop()

    depth = st.text_input("Depth (m)")

    try:
        depth = float(depth)
    except:
        st.stop()

    ct_vol = 0
    ann_vol = 0
    remaining = depth

    for sec in st.session_state.ct_strings[st.session_state.active_ct]:
        id_mm = sec["od"] - 2 * sec["wall"]
        ct_area = math.pi * ((id_mm / 2000) ** 2)

        casing = next(
            (c for c in st.session_state.well["casing"]
             if c["from"] <= (depth - remaining + 0.01) <= c["to"]), None
        )

        if not casing:
            break

        casing_area = math.pi * ((casing["id_mm"] / 2000) ** 2)
        length = min(sec["length"], remaining)

        ct_vol += ct_area * length
        ann_vol += (casing_area - math.pi * ((sec["od"] / 2000) ** 2)) * length
        remaining -= length

        if remaining <= 0:
            break

    st.success(f"CT Volume: {ct_vol:.3f} m³")
    st.success(f"Annular Volume: {ann_vol:.3f} m³")
    st.success(f"Total Circulating Volume: {(ct_vol + ann_vol):.3f} m³")

# ================== FLUIDS ==================
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
        base_density = st.number_input("Custom Density (kg/m³)", min_value=800.0)

    st.session_state.fluid["base_type"] = base_type
    st.session_state.fluid["base_density"] = base_density

    st.subheader("Add Chemical")

    c1, c2, c3 = st.columns(3)
    with c1:
        chem_name = st.text_input("Name")
    with c2:
        chem_density = st.number_input("Density (kg/m³)", min_value=500.0)
    with c3:
        chem_rate = st.number_input("Rate (L/m³)", min_value=0.0)

    if st.button("Add Chemical") and chem_name:
        st.session_state.fluid["chemicals"].append({
            "name": chem_name,
            "density": chem_density,
            "rate": chem_rate
        })

    total_rate = sum(c["rate"] for c in st.session_state.fluid["chemicals"])
    blended_density = (
        (base_density * (1000 - total_rate)) +
        sum(c["density"] * c["rate"] for c in st.session_state.fluid["chemicals"])
    ) / 1000

    st.success(f"Blended Density: {blended_density:.1f} kg/m³")

# ================== JOBS ==================
elif page == "💾 Jobs":
    st.header("Job Manager")

    name = st.text_input("Job Name", st.session_state.well.get("job_name", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Job") and name:
            st.session_state.well["job_name"] = name
            save_job(name)
            st.success("Job saved.")
    with col2:
        jobs = [f.replace(".json", "") for f in os.listdir(JOB_DIR)]
        selected = st.selectbox("Load Job", [""] + jobs)
        if st.button("📂 Load Job") and selected:
            load_job(selected)
            st.success("Job loaded.")

# ================== EXPORT ==================
elif page == "📤 Export":
    st.header("Export Job Summary")

    if not st.session_state.active_ct:
        st.warning("Select an active CT string.")
        st.stop()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Job", st.session_state.well.get("job_name", "")])
    writer.writerow(["Exported", datetime.now().isoformat()])
    st.download_button(
        "⬇️ Download CSV",
        output.getvalue(),
        file_name="job_summary.csv",
        mime="text/csv"
    )

# ================== SETTINGS ==================
elif page == "⚙️ Settings":
    st.header("Settings")
    st.session_state.settings["rate_unit"] = st.selectbox(
        "Rate Unit", ["m/min", "ft/min", "bbl/min"]
    )
    st.session_state.settings["force_unit"] = st.selectbox(
        "Force Unit", ["daN", "lbf"]
    )
