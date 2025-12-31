import streamlit as st
import math
from datetime import datetime
import base64
from pathlib import Path
import streamlit.components.v1 as components


st.set_page_config(
    page_title="WellOps",
    layout="wide"
)

with st.sidebar:
    st.image("assets/wellops_logo.png", use_column_width=True)
    
# =========================
# APP STATE (REQUIRED)
# =========================

def default_job():
    return {
        "meta": {
            "name": None,
            "last_modified": None
        },
        "ct": {
            "strings": [],
            "active_index": None
        },
        "well": {
            "tvd": None,
            "kop": None,
            "td": None,
            "casing": [],
            "restrictions": [],
            "schematic": None
        },
        "fluids": {
            "base": None,
            "density": None,
            "chemicals": []
        },
        "settings": {
            "units": "metric",
            "flow_unit": "m/min",
            "force_unit": "daN",
            "theme": "dark"
        }
    }

if "job" not in st.session_state:
    st.session_state.job = default_job()

job = st.session_state.job

def apply_theme(settings: dict):
    theme = settings.get("theme", "dark")
    accent = settings.get("accent_color", "#F97316")  # default orange

    if theme == "light":
        bg = "#F8FAFC"
        sidebar_bg = "#FFFFFF"
        text = "#0F172A"
        input_bg = "#FFFFFF"
        border = "#CBD5E1"
    else:
        bg = "#000000"
        sidebar_bg = "#0B1220"
        text = "#F9FAFB"
        input_bg = "#111827"
        border = "#374151"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
        }}

        button {{
            background-color: {accent} !important;
            color: white !important;
            border-radius: 8px !important;
            border: 0 !important;
        }}

        input, select, textarea {{
            background-color: {input_bg} !important;
            color: {text} !important;
            border: 1px solid {border} !important;
        }}

        h1, h2, h3, h4, p, span, label, div {{
            color: {text};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Defaults if missing (safe upgrade path)
job["settings"].setdefault("theme", "dark")
job["settings"].setdefault("accent_color", "#F97316")
job["settings"].setdefault("length_unit", "m")
job["settings"].setdefault("pressure_unit", "kPa")
job["settings"].setdefault("rate_unit", "m³/min")
job["settings"].setdefault("volume_unit", "m³")
job["settings"].setdefault("force_unit", "daN")
job["settings"].setdefault("decimals", 2)

apply_theme(job["settings"])

# =========================
# NAVIGATION
# =========================

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "CT Strings",
        "Well / Job",
        "Flow & Velocity",
        "Volumes",
        "Fluids",
        "Pressure",
        "Settings"
    ],
    format_func=lambda x: {
        "Home": "🏠 Home",
        "CT Strings": "🧵 CT Strings",
        "Well / Job": "🛢️ Well / Job",
        "Flow & Velocity": "🌀 Flow & Velocity",
        "Volumes": "🧊 Volumes",
        "Fluids": "🧪 Fluids",
        "Pressure":"📉 Pressure",
        "Settings": "⚙️ Settings"
    }[x]
)

if "page_override" in st.session_state:
    page = st.session_state.page_override
    del st.session_state.page_override

# =========================
# HOME
# =========================

if page == "Home":

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(
            "assets/wellops_logo.png",
            width=280
        )

    components.html(
        """
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 70vh;
            text-align: center;
        ">

            <div style="
                margin-top: 18px;
                font-size: 28px;
                font-weight: 600;
                color: #F97316;
            ">
                Plan. Verify. Execute.
            </div>

            <div style="
                margin-top: 16px;
                max-width: 720px;
                font-size: 19px;
                line-height: 1.7;
                color: #D1D5DB;
            ">
                Integrated calculations for flow, volumes, and pressure. 
                Purpose-built for coiled tubing and intervention operations
            </div>

        </div>
        """,
        height=500
    )

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])

    with c2:
        if st.button("🟧 Start New Job", use_container_width=True):
            st.session_state.page_override = "Well / Job"

        if st.button("Open Saved Job", use_container_width=True):
            st.info("Saved jobs coming next.")
    
# =========================
# CT STRINGS (FINAL, LOCKABLE)
# =========================

elif page == "CT Strings":
    st.header("CT String Builder")

    # ---- OD OPTIONS ----
    ct_od_options = {
        '1" – 25.4 mm': 25.4,
        '1-1/4" – 31.8 mm': 31.8,
        '1-1/2" – 38.1 mm': 38.1,
        '1-3/4" – 44.5 mm': 44.5,
        '2" – 50.8 mm': 50.8,
        '2-3/8" – 60.3 mm': 60.3,
        '2-7/8" – 73.0 mm': 73.0
    }

    # ---- CREATE STRING ----
    st.subheader("CT Strings")

    new_name = st.text_input("Create new CT string", value="")

    if st.button("Add CT String"):
        if new_name.strip():
            job["ct"]["strings"].append({
                "name": new_name.strip(),
                "sections": [],
                "ratings": {
                    "burst": None,
                    "collapse": None,
                    "pull": None
                }
            })
            job["ct"]["active_index"] = len(job["ct"]["strings"]) - 1

    if not job["ct"]["strings"]:
        st.info("Create a CT string to begin.")
        st.stop()

    names = [s["name"] for s in job["ct"]["strings"]]
    job["ct"]["active_index"] = st.selectbox(
        "Active CT String",
        range(len(names)),
        format_func=lambda i: names[i],
        index=job["ct"]["active_index"] or 0
    )

    ct = job["ct"]["strings"][job["ct"]["active_index"]]

    # ---- RATINGS (MANUAL) ----
    st.markdown("### CT Ratings (80%)")

    r1, r2, r3 = st.columns(3)

    with r1:
        burst = st.text_input("Burst (kPa)", value="")
    with r2:
        collapse = st.text_input("Collapse (kPa)", value="")
    with r3:
        pull = st.text_input("Max Pull (daN)", value="")

    if burst:
        ct["ratings"]["burst"] = float(burst)
    if collapse:
        ct["ratings"]["collapse"] = float(collapse)
    if pull:
        ct["ratings"]["pull"] = float(pull)

    # ---- ADD SECTION ----
    st.markdown("### Add Section (Whip → Core)")

    c1, c2, c3 = st.columns(3)

    with c1:
        sec_length_txt = st.text_input("Length (m)", value="", key="sec_len")
    with c2:
        sec_od_label = st.selectbox("OD", list(ct_od_options.keys()))
    with c3:
        sec_wall_txt = st.text_input("Wall thickness (mm)", value="", key="sec_wall")

    if st.button("Add Section"):
        if sec_length_txt and sec_wall_txt:
            sec_length = float(sec_length_txt)
            sec_wall = float(sec_wall_txt)

            ct["sections"].insert(0, {
                "length": sec_length,
                "od": ct_od_options[sec_od_label],
                "wall": sec_wall
            })
        else:
            st.warning("All fields must be filled.")

    # ---- DISPLAY SECTIONS ----
    if not ct["sections"]:
        st.info("No sections added yet.")
        st.stop()

    st.markdown("### Sections (Whip → Core)")

    total_length = 0.0
    internal_volume = 0.0
    displacement_volume = 0.0

    for i, sec in enumerate(ct["sections"]):
        id_mm = sec["od"] - 2 * sec["wall"]
        id_m = id_mm / 1000
        od_m = sec["od"] / 1000

        area_id = math.pi * (id_m / 2) ** 2
        area_od = math.pi * (od_m / 2) ** 2

        vol_internal = area_id * sec["length"]
        vol_disp = area_od * sec["length"]

        total_length += sec["length"]
        internal_volume += vol_internal
        displacement_volume += vol_disp

        with st.expander(f"Section {i+1} | {sec['length']} m | OD {sec['od']} mm"):
            st.write(f"Wall thickness: {sec['wall']} mm")
            st.write(f"Internal volume: {vol_internal:.3f} m³")
            st.write(f"Displacement volume: {vol_disp:.3f} m³")

            trim_txt = st.text_input(
                "Trim from whip end (m)",
                value="",
                key=f"trim_{i}"
            )

            if trim_txt:
                trim = float(trim_txt)
                if st.button("Apply Trim", key=f"apply_trim_{i}"):
                    sec["length"] -= trim
                    st.experimental_rerun()

            if st.button("Delete Section", key=f"delete_sec_{i}"):
                ct["sections"].pop(i)
                st.experimental_rerun()

    # ---- SUMMARY ----
    st.markdown("---")
    st.success(f"Total CT Length: {total_length:.1f} m")
    st.success(f"CT Internal Volume: {internal_volume:.3f} m³")
    st.success(f"CT Displacement Volume: {displacement_volume:.3f} m³")
        
# =========================
# WELL / JOB (RESTORED & CORRECT)
# =========================

elif page == "Well / Job":
    st.header("Well / Job Setup")

    # --- DEPTHS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        job["well"]["tvd"] = st.number_input("TVD (m)", value=job["well"]["tvd"])
    with c2:
        job["well"]["kop"] = st.number_input("KOP (m)", value=job["well"]["kop"])
    with c3:
        job["well"]["td"] = st.number_input("TD (m)", value=job["well"]["td"])

    # --- CASING / LINER ---
    st.subheader("Casing / Liner Sections")

    c1, c2, c3 = st.columns(3)
    with c1:
        top = st.number_input("Top depth (m)", min_value=0.0)
    with c2:
        bottom = st.number_input("Bottom depth (m)", min_value=0.0)
    with c3:
        id_mm = st.number_input("Internal diameter (mm)", min_value=0.0)

    if st.button("Add casing / liner section"):
        if bottom > top and id_mm > 0:
            job["well"]["casing"].append({
                "top": top,
                "bottom": bottom,
                "id": id_mm
            })

    for c in job["well"]["casing"]:
        st.write(f"{c['top']}–{c['bottom']} m | ID {c['id']} mm")

    # --- RESTRICTIONS ---
    st.subheader("Restrictions")

    r1, r2, r3 = st.columns(3)
    with r1:
        r_name = st.text_input("Restriction name (e.g. XN nipple)")
    with r2:
        r_depth = st.number_input("Restriction depth (m)", min_value=0.0)
    with r3:
        r_id = st.number_input("Restriction ID (mm)", min_value=0.0)

    if st.button("Add restriction"):
        if r_name and r_id > 0:
            job["well"]["restrictions"].append({
                "name": r_name,
                "depth": r_depth,
                "id": r_id
            })

    for r in job["well"]["restrictions"]:
        st.write(
            f"{r['name']} | Depth {r['depth']} m | ID {r['id']} mm"
        )

    # --- SCHEMATIC ---
    st.subheader("Well Schematic")
    job["well"]["schematic"] = st.file_uploader(
        "Upload schematic",
        type=["png", "jpg", "jpeg", "pdf"]
    )

# =========================
# FLOW & VELOCITY (SECTIONED + AVERAGE)
# =========================

elif page == "Flow & Velocity":

    st.header("🌀 Flow & Velocity")

    # --- Guardrails ---
    if job["ct"]["active_index"] is None or not job["ct"]["strings"]:
        st.info("Select an active CT string first (CT Strings page).")
        st.stop()

    if not job["well"]["casing"]:
        st.info("Add casing geometry first (Well / Job page).")
        st.stop()

    # --- Settings ---
    rate_unit = job["settings"].get("rate_unit", "m³/min")
    decimals = int(job["settings"].get("decimals", 2))

    # --- Inputs ---
    col1, col2 = st.columns(2)
    with col1:
        depth_m = st.number_input("Depth (m)", min_value=0.0, value=0.0, placeholder="Enter depth")
    with col2:
        rate_in = st.number_input(f"Pump rate ({rate_unit})", min_value=0.0, value=0.0, placeholder="Enter pump rate")

    # --- Convert rate -> m³/min ---
    if rate_unit == "L/min":
        rate_m3_min = rate_in / 1000.0
    elif rate_unit == "bbl/min":
        rate_m3_min = rate_in * 0.158987294928  # bbl -> m³
    else:
        rate_m3_min = rate_in

    # --- Active CT OD (OD constant across string) ---
    ct = job["ct"]["strings"][job["ct"]["active_index"]]
    ct_od_mm = ct["sections"][0]["od"]
    ct_od_m = ct_od_mm / 1000.0

    if depth_m <= 0 or rate_m3_min <= 0:
        st.info("Enter Depth and Pump rate to calculate annular velocity and bottoms-up time.")
        st.stop()

    # --- Determine casing at depth (for point velocity) ---
    casing_at_depth = next(
        (c for c in job["well"]["casing"] if c["top"] <= depth_m <= c["bottom"]),
        None
    )
    if casing_at_depth is None:
        st.warning("No casing section covers this depth. Check casing top/bottom depths in Well / Job.")
        st.stop()

    casing_id_m = casing_at_depth["id"] / 1000.0
    ann_area_m2 = math.pi * ((casing_id_m / 2) ** 2 - (ct_od_m / 2) ** 2)
    if ann_area_m2 <= 0:
        st.error("Annular area is ≤ 0. Check casing ID vs CT OD.")
        st.stop()

    vel_at_depth = rate_m3_min / ann_area_m2

    # --- Segment velocities + length-weighted average to depth ---
    casing_sorted = sorted(job["well"]["casing"], key=lambda x: x["top"])

    segments = []
    total_len = 0.0
    vel_len_sum = 0.0
    vol_to_depth_m3 = 0.0

    for c in casing_sorted:
        seg_top = max(0.0, float(c["top"]))
        seg_bot = float(c["bottom"])

        if seg_bot <= seg_top:
            continue

        seg_start = seg_top
        seg_end = min(depth_m, seg_bot)

        if seg_end <= seg_start:
            continue

        seg_len = seg_end - seg_start
        seg_id_m = float(c["id"]) / 1000.0

        seg_ann_area = math.pi * ((seg_id_m / 2) ** 2 - (ct_od_m / 2) ** 2)
        if seg_ann_area <= 0:
            continue

        seg_vel = rate_m3_min / seg_ann_area

        segments.append({
            "from": seg_start,
            "to": seg_end,
            "len": seg_len,
            "id_mm": float(c["id"]),
            "vel": seg_vel
        })

        total_len += seg_len
        vel_len_sum += seg_vel * seg_len
        vol_to_depth_m3 += seg_ann_area * seg_len

    avg_vel_to_depth = (vel_len_sum / total_len) if total_len > 0 else None
    bottoms_up_min = (vol_to_depth_m3 / rate_m3_min) if rate_m3_min > 0 else None

    # --- Output ---
    st.subheader("Results")

    st.success(f"Annular velocity at {depth_m:.0f} m: {vel_at_depth:.{decimals}f} m/min")
    st.caption(f"At depth uses casing ID {casing_at_depth['id']} mm and CT OD {ct_od_mm} mm.")

    # --- Compact mobile-friendly segment cards ---
    if segments:
        st.markdown("### Velocity by casing section (surface → depth)")

        for i, s in enumerate(segments, start=1):
            with st.container(border=True):
                left, right = st.columns([1, 1])

                with left:
                    st.markdown(f"**Section {i}**")
                    st.write(f"Depth: **{s['from']:.0f}–{s['to']:.0f} m**")
                    st.write(f"Casing ID: **{s['id_mm']:.1f} mm**")

                with right:
                    st.markdown("**Velocity**")
                    st.markdown(
                        f"<div style='font-size: 26px; font-weight: 800; color: #F9FAFB;'>"
                        f"{s['vel']:.{decimals}f} m/min</div>",
                        unsafe_allow_html=True
                    )
                    st.write(f"Length: **{s['len']:.0f} m**")

        if avg_vel_to_depth is not None:
            st.success(
                f"Average annular velocity (length-weighted) to {depth_m:.0f} m: "
                f"{avg_vel_to_depth:.{decimals}f} m/min"
            )

    if bottoms_up_min is not None:
        st.success(f"Bottoms-up time to {depth_m:.0f} m: {bottoms_up_min:.{decimals}f} min")
        st.caption("Calculated from annular volume (surface → depth) ÷ pump rate.")
# =========================
# Volumes
# =========================

elif page == "Volumes":
    st.header("🧊 Volumes")

    # --- Guards ---
    if (
        job["ct"]["active_index"] is None
        or not job["ct"]["strings"]
        or not job["ct"]["strings"][job["ct"]["active_index"]].get("sections")
        or not job["well"]["casing"]
        or job["well"].get("td") is None
    ):
        st.info("Define CT string and well geometry first.")
        st.stop()

    ct = job["ct"]["strings"][job["ct"]["active_index"]]
    td = float(job["well"]["td"])

    # --- Settings ---
    volume_unit = job["settings"].get("volume_unit", "m³")
    decimals = int(job["settings"].get("decimals", 2))

    def m3_to_unit(m3: float) -> float:
        if volume_unit == "L":
            return m3 * 1000.0
        if volume_unit == "bbl":
            return m3 / 0.158987294928
        return m3

    def unit_label() -> str:
        return volume_unit

    # --- CT geometry (OD constant across string) ---
    ct_od_m = float(ct["sections"][0]["od"]) / 1000.0
    ct_od_area = math.pi * (ct_od_m / 2.0) ** 2

    # --- Total CT length + TOTAL CT internal volume (full string) ---
    ct_total_len = 0.0
    ct_internal_total_m3 = 0.0

    for sec in ct["sections"]:
        sec_len = float(sec["length"])
        ct_total_len += sec_len

        id_mm = float(sec["od"]) - 2.0 * float(sec["wall"])
        id_m = max(id_mm, 0.0) / 1000.0
        area = math.pi * (id_m / 2.0) ** 2
        ct_internal_total_m3 += area * sec_len

    # =========================
    # Helper: Hole + Annular volume to a depth (segmented casing)
    # =========================
    def hole_and_annular_to_depth(depth_m: float):
        hole_m3 = 0.0
        ann_m3 = 0.0

        casing_sorted = sorted(job["well"]["casing"], key=lambda x: x["top"])

        for c in casing_sorted:
            top = float(c["top"])
            bottom = float(c["bottom"])

            seg_start = max(0.0, top)
            seg_end = min(depth_m, bottom)

            if seg_end <= seg_start:
                continue

            seg_len = seg_end - seg_start
            casing_id_m = float(c["id"]) / 1000.0
            casing_area = math.pi * (casing_id_m / 2.0) ** 2

            hole_m3 += casing_area * seg_len

            seg_ann_area = casing_area - ct_od_area
            if seg_ann_area > 0:
                ann_m3 += seg_ann_area * seg_len

        return hole_m3, ann_m3

    # =========================
    # A (Always On): Volumes to TD
    # =========================
    depth_A = td

    hole_A, ann_A = hole_and_annular_to_depth(depth_A)

    # CT displacement depends on how much CT is actually in hole
    ct_run_len_A = min(depth_A, ct_total_len)
    ct_displacement_A = ct_od_area * ct_run_len_A

    total_circ_A = ct_internal_total_m3 + ann_A

    st.subheader("A — Volumes to TD")

    st.success(f"CT Internal Volume (total string): {m3_to_unit(ct_internal_total_m3):.{decimals}f} {unit_label()}")
    st.success(f"CT Displacement (to TD): {m3_to_unit(ct_displacement_A):.{decimals}f} {unit_label()}")
    st.success(f"Annular Volume (to TD): {m3_to_unit(ann_A):.{decimals}f} {unit_label()}")
    st.success(f"Hole Volume (to TD): {m3_to_unit(hole_A):.{decimals}f} {unit_label()}")
    st.success(f"Total Circulating Volume (to TD): {m3_to_unit(total_circ_A):.{decimals}f} {unit_label()}")

    # =========================
    # B (Precise): Volumes to Specific Depth
    # =========================
    with st.expander("B — Advanced: Volumes to Specific Depth"):
        depth_input = st.text_input("Depth (m)", value="")

        try:
            depth_B = float(depth_input)
            valid_depth = 0 < depth_B <= td
        except:
            valid_depth = False

        if not valid_depth:
            st.info("Enter a valid depth within TD.")
        else:
            hole_B, ann_B = hole_and_annular_to_depth(depth_B)

            ct_run_len_B = min(depth_B, ct_total_len)
            ct_displacement_B = ct_od_area * ct_run_len_B

            total_circ_B = ct_internal_total_m3 + ann_B

            st.markdown("### Volumes to Depth")
            st.write(f"Depth: **{depth_B:.0f} m**")

            st.success(f"CT Internal Volume (total string): {m3_to_unit(ct_internal_total_m3):.{decimals}f} {unit_label()}")
            st.success(f"CT Displacement: {m3_to_unit(ct_displacement_B):.{decimals}f} {unit_label()}")
            st.success(f"Annular Volume: {m3_to_unit(ann_B):.{decimals}f} {unit_label()}")
            st.success(f"Hole Volume: {m3_to_unit(hole_B):.{decimals}f} {unit_label()}")
            st.success(f"Total Circulating Volume: {m3_to_unit(total_circ_B):.{decimals}f} {unit_label()}")
            
# =========================
# FLUIDS
# =========================

elif page == "Fluids":

    st.header("🧪 Fluids")

    st.subheader("Base Fluid")

    base_fluid = st.selectbox(
        "Select base fluid",
        ["Fresh Water", "Produced Water", "Custom"]
    )

    if base_fluid == "Fresh Water":
        base_density = 1000.0  # kg/m³
        st.info("Fresh water density assumed: 1000 kg/m³")

    elif base_fluid == "Produced Water":
        base_density = 1100.0  # kg/m³ (average)
        st.info("Produced water density assumed: 1100 kg/m³")

    else:
        base_density = st.number_input(
            "Custom base fluid density (kg/m³)",
            min_value=500.0,
            max_value=2000.0,
            step=1.0
        )

    job["fluids"]["base"] = base_fluid

    # -------------------------
    # Chemicals
    # -------------------------

    st.subheader("Chemicals")

    chem_name = st.text_input("Chemical name")
    chem_density = st.number_input(
        "Chemical density (kg/m³)",
        min_value=500.0,
        max_value=3000.0,
        step=1.0
    )
    chem_rate = st.number_input(
        "Concentration (L/m³)",
        min_value=0.0,
        step=0.1
    )

    if st.button("Add chemical"):
        if chem_name and chem_rate > 0:
            job["fluids"]["chemicals"].append({
                "name": chem_name,
                "density": chem_density,
                "rate": chem_rate
            })

    # -------------------------
    # Blended Density
    # -------------------------

    total_volume = 1.0  # 1 m³ reference
    total_mass = base_density * total_volume

    for chem in job["fluids"]["chemicals"]:
        chem_vol = chem["rate"] / 1000  # L → m³
        chem_mass = chem_vol * chem["density"]

        total_volume += chem_vol
        total_mass += chem_mass

        st.write(
            f"{chem['name']}: "
            f"{chem['rate']} L/m³ | "
            f"{chem['density']} kg/m³"
        )

    blended_density = total_mass / total_volume

    job["fluids"]["density"] = base_density
    job["fluids"]["blended_density"] = blended_density

    # -------------------------
    # Results
    # -------------------------

    st.markdown("---")
    st.subheader("Results")

    st.metric("Blended Fluid Density", f"{blended_density:.1f} kg/m³")

# =========================
# HYDROSTATIC PRESSURE
# =========================

elif page == "Pressure":

    st.header("📉 Pressure — Hydrostatic")

    # --- Settings ---
    pressure_unit = job["settings"].get("pressure_unit", "kPa")
    decimals = int(job["settings"].get("decimals", 2))

    # --- Pull blended density from Fluids page (supports common keys) ---
    blended_density = (
        job.get("fluids", {}).get("blended_density_kg_m3")
        or job.get("fluids", {}).get("blended_density")
        or job.get("fluids", {}).get("density")
    )

    # --- Default TVD from Well / Job ---
    default_tvd = job.get("well", {}).get("tvd")

    # --- Inputs ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Depth")
        use_tvd = st.checkbox("Use TVD from Well / Job", value=True)

        if use_tvd and default_tvd is not None:
            depth_m = st.number_input(
                "TVD (m)",
                value=float(default_tvd),
                min_value=0.0
            )
        else:
            depth_m = st.number_input(
                "Depth (m)",
                value=0.0,
                min_value=0.0,
                placeholder="Enter depth"
            )

    with col2:
        st.subheader("Fluid Density")
        use_blended = st.checkbox("Use blended density from Fluids", value=True)

        if use_blended and blended_density is not None:
            rho = st.number_input(
                "Density (kg/m³)",
                value=float(blended_density),
                min_value=0.0
            )
        else:
            rho = st.number_input(
                "Density (kg/m³)",
                value=0.0,
                min_value=0.0,
                placeholder="Enter density"
            )

    # --- Guidance if missing sources ---
    if use_tvd and default_tvd is None:
        st.warning("No TVD set in Well / Job. Either set TVD there or uncheck 'Use TVD' and enter a depth.")

    if use_blended and blended_density is None:
        st.warning("No blended density set in Fluids. Either set it in Fluids or uncheck 'Use blended density' and enter a density.")

    # --- Calculate ---
    if depth_m > 0 and rho > 0:
        g = 9.80665  # m/s²
        p_pa = rho * g * depth_m  # Pascals

        # Convert pressure
        if pressure_unit == "psi":
            p_out = p_pa / 6894.757293168
            unit = "psi"
        else:
            p_out = p_pa / 1000.0
            unit = "kPa"

        # Gradient (optional but useful)
        grad_kpa_m = (rho * g) / 1000.0
        grad_psi_ft = (rho * g) / 6894.757293168 / 3.280839895

        st.subheader("Results")
        st.success(f"Hydrostatic pressure: {p_out:.{decimals}f} {unit}")

        with st.expander("Show gradients"):
            st.write(f"Gradient: **{grad_kpa_m:.{decimals}f} kPa/m**")
            st.write(f"Gradient: **{grad_psi_ft:.{decimals}f} psi/ft**")

    else:
        st.info("Enter a valid Depth and Density to calculate hydrostatic pressure.")
        
# =========================
# SETTINGS
# =========================

elif page == "Settings":

    st.header("⚙️ Settings")

    col1, col2 = st.columns(2)

    with col1:
        job["settings"]["theme"] = st.selectbox(
            "Theme",
            ["dark", "light"],
            index=0 if job["settings"]["theme"] == "dark" else 1
        )

        job["settings"]["accent_color"] = st.selectbox(
            "Accent colour",
            ["#F97316  (Orange)", "#00E676  (Neon Green)", "#3B82F6  (Blue)"],
            index=0 if job["settings"]["accent_color"] == "#F97316" else
                  1 if job["settings"]["accent_color"] == "#00E676" else 2
        ).split()[0]  # grab hex only

        job["settings"]["decimals"] = st.slider(
            "Decimal places",
            min_value=0,
            max_value=4,
            value=int(job["settings"]["decimals"])
        )

    with col2:
        st.subheader("Units (future-proofed)")

        job["settings"]["length_unit"] = st.selectbox(
            "Length",
            ["m", "ft"],
            index=0 if job["settings"]["length_unit"] == "m" else 1
        )

        job["settings"]["pressure_unit"] = st.selectbox(
            "Pressure",
            ["kPa", "psi"],
            index=0 if job["settings"]["pressure_unit"] == "kPa" else 1
        )

        job["settings"]["rate_unit"] = st.selectbox(
            "Pump rate",
            ["m³/min", "L/min", "bbl/min"],
            index=["m³/min", "L/min", "bbl/min"].index(job["settings"]["rate_unit"])
        )

        job["settings"]["volume_unit"] = st.selectbox(
            "Volume",
            ["m³", "L", "bbl"],
            index=["m³", "L", "bbl"].index(job["settings"]["volume_unit"])
        )

        job["settings"]["force_unit"] = st.selectbox(
            "Pull / Force",
            ["daN", "lbf"],
            index=0 if job["settings"]["force_unit"] == "daN" else 1
        )

    st.divider()
    st.info("Settings apply immediately. Units conversion will be wired page-by-page next.")
    apply_theme(job["settings"])
