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
                Plan. Execute. Verify.
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
    st.header("Flow & Annular Velocity")

    if (
        job["ct"]["active_index"] is None
        or not job["ct"]["strings"][job["ct"]["active_index"]]["sections"]
        or not job["well"]["casing"]
    ):
        st.info("Define CT string and well geometry first.")
    else:
        ct = job["ct"]["strings"][job["ct"]["active_index"]]
        ct_od_m = ct["sections"][0]["od"] / 1000  # OD constant

        col1, col2 = st.columns(2)

        with col1:
            depth_input = st.text_input("Depth (m)")
        with col2:
            rate_input = st.text_input("Pump rate (m³/min)")

        try:
            depth = float(depth_input)
            pump_rate = float(rate_input)
            valid = depth > 0 and pump_rate > 0
        except (ValueError, TypeError):
            valid = False

        if not valid:
            st.info("Enter valid depth and pump rate to calculate velocity.")
        else:
            st.subheader("Annular Velocity by Casing Section")

            total_annular_volume = 0.0
            velocity_volume_sum = 0.0
            point_velocity = None

            for c in job["well"]["casing"]:
                section_length = c["bottom"] - c["top"]
                casing_id_m = c["id"] / 1000

                ann_area = math.pi * (
                    (casing_id_m / 2) ** 2 - (ct_od_m / 2) ** 2
                )

                if ann_area <= 0:
                    st.error(
                        f"Invalid annulus for casing ID {c['id']} mm"
                    )
                    continue

                velocity = pump_rate / ann_area
                section_volume = ann_area * section_length

                total_annular_volume += section_volume
                velocity_volume_sum += velocity * section_volume

                if c["top"] <= depth <= c["bottom"]:
                    point_velocity = velocity

                st.write(
                    f"{c['id']} mm casing | "
                    f"{c['top']:.0f}–{c['bottom']:.0f} m | "
                    f"Velocity: {velocity:.2f} m/min"
                )

            avg_velocity = velocity_volume_sum / total_annular_volume
            bottoms_up_time = total_annular_volume / pump_rate

            st.markdown("---")
            st.subheader("Results")

            if point_velocity is not None:
                st.success(
                    f"Annular Velocity at {depth:.0f} m: "
                    f"{point_velocity:.2f} m/min"
                )
            else:
                st.warning("Depth is outside defined casing sections.")

            st.success(
                f"Average Annular Velocity: {avg_velocity:.2f} m/min"
            )
            st.success(
                f"Bottoms Up Time: {bottoms_up_time:.1f} minutes"
            )

# =========================
# Volumes
# =========================

elif page == "Volumes":
    st.header("Volumes")

    # --- Guards ---
    if (
        job["ct"]["active_index"] is None
        or not job["ct"]["strings"][job["ct"]["active_index"]]["sections"]
        or not job["well"]["casing"]
        or job["well"]["td"] is None
    ):
        st.info("Define CT string and well geometry first.")
    else:
        ct = job["ct"]["strings"][job["ct"]["active_index"]]
        td = job["well"]["td"]

        # =========================
        # CT INTERNAL VOLUME
        # =========================
        ct_internal_vol = 0.0
        for sec in ct["sections"]:
            id_m = (sec["od"] - 2 * sec["wall"]) / 1000
            area = math.pi * (id_m / 2) ** 2
            ct_internal_vol += area * sec["length"]

        # =========================
        # ANNULAR + HOLE VOLUMES (to TD)
        # =========================
        annular_vol = 0.0
        hole_vol = 0.0

        ct_od_m = ct["sections"][0]["od"] / 1000  # OD constant

        for c in job["well"]["casing"]:
            top = c["top"]
            bottom = min(c["bottom"], td)

            if bottom <= top:
                continue

            length = bottom - top
            casing_id_m = c["id"] / 1000

            casing_area = math.pi * (casing_id_m / 2) ** 2
            ct_area = math.pi * (ct_od_m / 2) ** 2

            hole_vol += casing_area * length
            annular_vol += (casing_area - ct_area) * length

        # =========================
        # CT DISPLACEMENT
        # =========================
        ct_displacement = hole_vol - annular_vol

        total_circ_vol = ct_internal_vol + annular_vol

        # =========================
        # DISPLAY — A (Always On)
        # =========================
        st.subheader("Volumes to TD")

        st.success(f"CT Internal Volume: {ct_internal_vol:.3f} m³")
        st.success(f"CT Displacement: {ct_displacement:.3f} m³")
        st.success(f"Annular Volume (to TD): {annular_vol:.3f} m³")
        st.success(f"Hole Volume (to TD): {hole_vol:.3f} m³")
        st.success(f"Total Circulating Volume: {total_circ_vol:.3f} m³")

        # =========================
        # B — ADVANCED / PRECISE
        # =========================
        with st.expander("Advanced: Volumes to Specific Depth"):
            depth_input = st.text_input("Depth (m)")

            try:
                depth = float(depth_input)
                valid_depth = 0 < depth <= td
            except:
                valid_depth = False

            if not valid_depth:
                st.info("Enter a valid depth within TD.")
            else:
                ann_vol_d = 0.0
                hole_vol_d = 0.0

                for c in job["well"]["casing"]:
                    top = c["top"]
                    bottom = min(c["bottom"], depth)

                    if bottom <= top:
                        continue

                    length = bottom - top
                    casing_id_m = c["id"] / 1000

                    casing_area = math.pi * (casing_id_m / 2) ** 2
                    ct_area = math.pi * (ct_od_m / 2) ** 2

                    hole_vol_d += casing_area * length
                    ann_vol_d += (casing_area - ct_area) * length

                ct_disp_d = hole_vol_d - ann_vol_d
                total_circ_d = ct_internal_vol + ann_vol_d

                st.markdown("### Volumes to Depth")
                st.write(f"Depth: {depth:.0f} m")

                st.success(f"Annular Volume: {ann_vol_d:.3f} m³")
                st.success(f"CT Displacement: {ct_disp_d:.3f} m³")
                st.success(f"Hole Volume: {hole_vol_d:.3f} m³")
                st.success(f"Total Circulating Volume: {total_circ_d:.3f} m³")

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

    st.header("📉 Hydrostatic Pressure")

    # --- Preconditions ---
    if job["well"]["tvd"] is None:
        st.warning("TVD not set in Well / Job page.")
        st.stop()

    if job["fluids"].get("blended_density") is None:
        st.warning("Blended fluid density not set in Fluids page.")
        st.stop()

    # --- Inputs ---
    st.subheader("Inputs")

    use_override = st.checkbox("Override depth")

    if use_override:
        depth = st.number_input(
            "Depth used for calculation (m)",
            min_value=0.0
        )
    else:
        depth = job["well"]["tvd"]
        st.info(f"Using TVD from Well / Job: {depth} m")

    density = job["fluids"]["blended_density"]
    st.write(f"Blended fluid density: **{density:.1f} kg/m³**")

    # --- Calculation ---
    g = 9.81  # m/s²

    pressure_pa = density * g * depth
    pressure_kpa = pressure_pa / 1_000
    pressure_mpa = pressure_pa / 1_000_000
    pressure_bar = pressure_pa / 100_000
    gradient_kpa_m = pressure_kpa / depth if depth > 0 else 0

    # --- Results ---
    st.subheader("Results")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Hydrostatic Pressure", f"{pressure_kpa:,.0f} kPa")
    with c2:
        st.metric("Hydrostatic Pressure", f"{pressure_mpa:.2f} MPa")
    with c3:
        st.metric("Hydrostatic Pressure", f"{pressure_bar:.2f} bar")

    st.metric("Pressure Gradient", f"{gradient_kpa_m:.2f} kPa/m")
        
# =========================
# SETTINGS
# =========================

elif page == "Settings":
    st.header("Settings")
    job["settings"]["theme"] = st.selectbox(
        "Theme",
        ["dark", "light"],
        index=0 if job["settings"]["theme"] == "dark" else 1
    )
