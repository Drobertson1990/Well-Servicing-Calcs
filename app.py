import streamlit as st
import math
import json
import os
from datetime import datetime
import csv
import io

# ================= CONFIG =================
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

# ================= STATE INIT =================
def init_state():
    st.session_state.setdefault("settings", {"rate_unit": "m³/min"})
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

# ================= JOB IO =================
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

    for key in job:
        st.session_state[key] = job[key]

# ================= HELPERS =================
def blended_fluid_density():
    base_density = st.session_state.fluid["base_density"]
    total_fraction = 1.0
    weighted_density = base_density

    for chem in st.session_state.fluid["chemicals"]:
        frac = chem["fraction"]
        weighted_density += frac * chem["density"]
        total_fraction += frac

    return weighted_density / total_fraction

# ================= HEADER =================
st.title("Well Servicing Calculator")
st.subheader("Coiled Tubing • Service Rigs • Snubbing")

# ================= NAV =================
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🛢️ Well / Job",
        "🧵 CT String Builder",
        "🌀 Annular Velocity",
        "🧊 Volumes & Displacement",
        "🧪 Fluids",
        "💾 Jobs",
        "📤 Export",
        "⚙️ Settings"
    ],
    label_visibility="collapsed"
)

# ================= HOME =================
if page == "🏠 Home":
    st.success("Geometry-driven calculations. Enter data once, reuse everywhere.")

# ================= WELL / JOB =================
elif page == "🛢️ Well / Job":
    st.header("Well / Job Setup")

    st.session_state.well["job_name"] = st.text_input("Job Name", st.session_state.well["job_name"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.well["tvd"] = st.text_input("TVD (m)", st.session_state.well["tvd"])
    with col2:
        st.session_state.well["kop"] = st.text_input("KOP (m)", st.session_state.well["kop"])
    with col3:
        st.session_state.well["td"] = st.text_input("TD (m)", st.session_state.well["td"])

    st.subheader("Casing / Liner Sections")

    with st.expander("Add Section"):
        c_from = st.text_input("From (m)")
        c_to = st.text_input("To (m)")
        c_id = st.text_input("ID (mm)")
        c_type = st.selectbox("Type", ["Casing", "Liner"])

        if st.button("Add Section"):
            try:
                st.session_state.well["casing"].append({
                    "from": float(c_from),
                    "to": float(c_to),
                    "id_mm": float(c_id),
                    "type": c_type
                })
                st.success("Section added.")
            except:
                st.error("Invalid casing data.")

    for i, c in enumerate(st.session_state.well["casing"], 1):
        st.write(f"{i}. {c['type']} {c['from']}–{c['to']} m | ID {c['id_mm']} mm")

# ================= CT STRING BUILDER =================
elif page == "🧵 CT String Builder":
    st.header("CT String Builder (Whip → Core)")

    name = st.text_input("CT String Name")

    col1, col2, col3 = st.columns(3)
    with col1:
        length = st.text_input("Section Length (m)")
    with col2:
        od_label = st.selectbox("OD", list(CT_OD_PRESETS.keys()))
    with col3:
        wall = st.text_input("Wall Thickness (mm)")

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
            list(st.session_state.ct_strings.keys())
        )

# ================= ANNULAR VELOCITY =================
elif page == "🌀 Annular Velocity":
    st.header("Annular Velocity (Depth + Rate Only)")

    if not st.session_state.active_ct or not st.session_state.well["casing"]:
        st.warning("Define casing and select an active CT string.")
        st.stop()

    depth = st.number_input("Depth (m)", min_value=0.0)
    rate = st.number_input("Pump Rate (m³/min)", min_value=0.0)

    casing = next((c for c in st.session_state.well["casing"]
                    if c["from"] <= depth <= c["to"]), None)

    remaining = depth
    ct_od = None
    for sec in st.session_state.ct_strings[st.session_state.active_ct]:
        if remaining <= sec["length"]:
            ct_od = sec["od"]
            break
        remaining -= sec["length"]

    if not casing or not ct_od:
        st.error("Invalid depth.")
        st.stop()

    casing_area = math.pi * (casing["id_mm"] / 2000) ** 2
    ct_area = math.pi * (ct_od / 2000) ** 2
    ann_area = casing_area - ct_area

    velocity = rate / ann_area
    st.success(f"Annular Velocity: {velocity:.2f} m/min")

# ================= VOLUMES & CT DISPLACEMENT =================
elif page == "🧊 Volumes & Displacement":
    st.header("Volumes & CT Displacement")

    if not st.session_state.active_ct:
        st.warning("Select an active CT string.")
        st.stop()

    depth = st.number_input("Depth (m)", min_value=0.0)

    ct_vol = 0.0
    ann_vol = 0.0
    disp_per_m = 0.0
    remaining = depth

    for sec in st.session_state.ct_strings[st.session_state.active_ct]:
        id_mm = sec["od"] - 2 * sec["wall"]
        ct_area = math.pi * (id_mm / 2000) ** 2
        od_area = math.pi * (sec["od"] / 2000) ** 2

        casing = next((c for c in st.session_state.well["casing"]
                        if c["from"] <= (depth - remaining + 0.01) <= c["to"]), None)
        if not casing:
            break

        casing_area = math.pi * (casing["id_mm"] / 2000) ** 2
        length = min(sec["length"], remaining)

        ct_vol += ct_area * length
        ann_vol += (casing_area - od_area) * length
        disp_per_m = od_area

        remaining -= length
        if remaining <= 0:
            break

    st.success(f"CT Internal Volume: {ct_vol:.3f} m³")
    st.success(f"Annular Volume: {ann_vol:.3f} m³")
    st.success(f"Total Circulating Volume: {(ct_vol + ann_vol):.3f} m³")
    st.info(f"CT Displacement: {disp_per_m:.4f} m³ per meter")

# ================= FLUIDS =================
elif page == "🧪 Fluids":
    st.header("Fluids & Chemicals")

    base = st.selectbox("Base Fluid", ["Fresh Water", "Produced Water", "Custom"])

    if base == "Fresh Water":
        density = FRESH_WATER_DENSITY
    elif base == "Produced Water":
        density = PRODUCED_WATER_DENSITY
    else:
        density = st.number_input("Custom Density (kg/m³)", min_value=800.0)

    st.session_state.fluid["base_type"] = base
    st.session_state.fluid["base_density"] = density

    st.subheader("Add Chemical")

    col1, col2, col3 = st.columns(3)
    with col1:
        chem_name = st.text_input("Name")
    with col2:
        chem_density = st.number_input("Density (kg/m³)", min_value=500.0)
    with col3:
        chem_frac = st.number_input("Mix Fraction (e.g. 0.05)", min_value=0.0)

    if st.button("Add Chemical"):
        st.session_state.fluid["chemicals"].append({
            "name": chem_name,
            "density": chem_density,
            "fraction": chem_frac
        })

    for i, chem in enumerate(st.session_state.fluid["chemicals"], 1):
        st.write(f"{i}. {chem['name']} | {chem['fraction']} @ {chem['density']} kg/m³")

    blended = blended_fluid_density()
    st.success(f"Blended Fluid Density: {blended:.1f} kg/m³")

# ================= JOBS =================
elif page == "💾 Jobs":
    st.header("Jobs")

    name = st.text_input("Job Name", st.session_state.well["job_name"])
    if st.button("Save Job"):
        save_job(name)
        st.success("Job saved.")

    jobs = [f.replace(".json", "") for f in os.listdir(JOB_DIR)]
    selected = st.selectbox("Load Job", [""] + jobs)

    if st.button("Load Job") and selected:
        load_job(selected)
        st.success("Job loaded.")

# ================= EXPORT =================
elif page == "📤 Export":
    st.header("Export Job Summary")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Job", st.session_state.well["job_name"]])
    writer.writerow(["Exported", datetime.now().isoformat()])

    st.download_button(
        "Download CSV",
        output.getvalue(),
        file_name="job_summary.csv",
        mime="text/csv"
    )

# ================= SETTINGS =================
elif page == "⚙️ Settings":
    st.header("Settings")
    st.session_state.settings["rate_unit"] = st.selectbox(
        "Pump Rate Unit",
        ["m³/min", "bbl/min"]
    )
