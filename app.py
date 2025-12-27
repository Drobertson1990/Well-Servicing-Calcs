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
    writer.writerow(["Base Density (kg/m³)", st.session_state.fluid["base_density"]])

    for chem in st.session_state.fluid["chemicals"]:
        writer.writerow([
            "Chemical",
            chem["name"],
            chem["density"],
            chem["rate"]
        ])

    return output.getvalue()

def generate_text_report():
    w = st.session_state.well
    ct_name = st.session_state.active_ct
    ct = st.session_state.ct_strings.get(ct_name, [])

    lines = []
    lines.append("WELL SERVICING JOB SUMMARY")
    lines.append("=" * 40)
    lines.append(f"Job Name: {w.get('job_name', '')}")
    lines.append(f"Exported: {datetime.now().isoformat()}")
    lines.append("")

    lines.append("WELL INFO")
    lines.append(f"TVD: {w.get('tvd', '')} m")
    lines.append(f"KOP: {w.get('kop', '')} m")
    lines.append(f"TD: {w.get('td', '')} m")
    lines.append("")

    lines.append("CASING / LINER")
    for c in w.get("casing", []):
        lines.append(f"{c['type']} {c['from']}–{c['to']} m | ID {c['id_mm']} mm")

    lines.append("")
    lines.append(f"CT STRING: {ct_name}")
    total_length = 0
    for i, sec in enumerate(ct, 1):
        total_length += sec["length"]
        lines.append(
            f"{i}. {sec['length']} m | OD {sec['od']} mm | Wall {sec['wall']} mm"
        )
    lines.append(f"Total Length: {total_length:.1f} m")

    lines.append("")
    lines.append("FLUID SYSTEM")
    lines.append(f"Base Density: {st.session_state.fluid['base_density']} kg/m³")

    for chem in st.session_state.fluid["chemicals"]:
        lines.append(
            f"{chem['name']} @ {chem['rate']} L/m³ | Density {chem['density']} kg/m³"
        )

    return "\n".join(lines)

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

# ---------------- EXPORT PAGE ----------------
if page == "📤 Export":
    st.header("Export Job Summary")

    if not st.session_state.active_ct:
        st.warning("Select an active CT string before exporting.")
        st.stop()

    csv_data = generate_csv()
    text_report = generate_text_report()

    st.download_button(
        "⬇️ Download CSV (Excel)",
        csv_data,
        file_name=f"{st.session_state.well.get('job_name','job')}_summary.csv",
        mime="text/csv"
    )

    st.download_button(
        "⬇️ Download Text Report",
        text_report,
        file_name=f"{st.session_state.well.get('job_name','job')}_summary.txt",
        mime="text/plain"
    )

# ---------------- PLACEHOLDERS ----------------
elif page != "📤 Export":
    st.info("This page remains unchanged from previous steps.")
