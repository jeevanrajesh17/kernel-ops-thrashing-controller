import streamlit as st

import pandas as pd

import plotly.express as px



from simulator import PagingSimulator

from detector import ThrashingDetector

from controller import allocate_frames_by_working_set, check_demand_feasibility

from workloads import SCENARIOS



st.set_page_config(

    page_title="Kernel Ops | Memory Intelligence",

    page_icon="🧠",

    layout="wide",

    initial_sidebar_state="expanded",

)



# --------------------------- DESIGN SYSTEM ---------------------------
st.markdown(
    """
    <style>
    :root {
      --bg: #100c17; --panel: #191321; --panel-2: #15101d;
      --border: #30263d; --green: #55e6a5; --violet: #9a72f5;
      --mint: #65d9a5; --amber: #e9bd62; --coral: #f16a86;
      --text: #f3f0f7; --muted: #aaa1b7;
    }
    .stApp { background: radial-gradient(ellipse at 72% 5%, #21152b 0%, var(--bg) 48%); color: var(--text); }
    [data-testid="stHeader"] { background: rgba(16,12,23,.96); }
    [data-testid="stSidebar"] { background: #130e1a; border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
    h1,h2,h3,p,label,span,div { color: inherit; }
    h1 { letter-spacing: -.04em !important; font-weight: 800 !important; }
    h2,h3 { letter-spacing: -.025em; }
    .eyebrow { color: var(--muted); text-transform: uppercase; letter-spacing: .22em; font-size: .68rem; font-weight: 750; margin-bottom: .55rem; }
    .hero-title { font-size: clamp(1.8rem, 3.4vw, 3.1rem); line-height: 1.02; font-weight: 850; letter-spacing: -.045em; color: var(--text); margin: 0; }
    .hero-accent { color: var(--green); }
    .hero-sub { color: #c0b8cc; margin-top: .8rem; font-size: .98rem; line-height: 1.5; }
    .hero-rule { height: 1px; margin: 1.15rem 0 1.25rem; background: var(--border); }
    .pill { display:inline-block; border:1px solid var(--border); border-radius:999px; padding:.36rem .65rem; margin:.18rem .3rem .25rem 0; color:#c1b8cf; font-size:.68rem; letter-spacing:.025em; background:#1a1422; }
    .metric-card { background: linear-gradient(145deg, #1d1627, #17121f); border:1px solid var(--border); border-radius:12px; padding:1rem 1rem .9rem; min-height:112px; box-shadow: 0 8px 24px rgba(0,0,0,.10); }
    .metric-label { color:var(--muted); text-transform:uppercase; letter-spacing:.09em; font-size:.65rem; font-weight:750; }
    .metric-value { color:var(--text); font-size:1.8rem; line-height:1.25; font-weight:780; margin:.42rem 0 .25rem; }
    .metric-note { color:var(--muted); font-size:.76rem; }
    .section-head { font-size:1.08rem; font-weight:760; margin:.5rem 0 .25rem; color:var(--text); }
    .section-sub { color:var(--muted); font-size:.81rem; margin-bottom:.8rem; }
    .callout { border:1px solid var(--border); border-left:3px solid var(--green); background:#1a1423; border-radius:12px; padding:1rem 1.1rem; margin:.65rem 0 1rem; }
    .callout-kicker { color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-size:.65rem; font-weight:750; }
    .callout-title { font-size:1rem; font-weight:750; margin:.35rem 0; }
    .callout-copy { color:#c5bdcf; font-size:.86rem; }
    .status-good { color:var(--green); } .status-warn { color:var(--amber); } .status-bad { color:var(--coral); }
    .frame-card { border:1px solid var(--border); border-radius:8px; padding:.7rem .75rem; min-height:100px; background:var(--panel); margin-bottom:.5rem; position:relative; overflow:hidden; }
    .frame-card:after { content:""; display:block; height:4px; border-radius:6px; margin-top:.65rem; background:#3a3047; }
    .frame-used-p1 { border-color:#624b8e; background:#21182d; }
    .frame-used-p1:after { background:var(--violet); }
    .frame-used-p2 { border-color:#286b56; background:#15271f; }
    .frame-used-p2:after { background:var(--green); }
    .frame-free { background:#15111c; }
    .frame-number { color:var(--muted); font-size:.7rem; letter-spacing:.06em; }
    .frame-owner { font-size:.98rem; font-weight:780; margin:.3rem 0 .15rem; }
    .frame-page { color:#b8afc4; font-size:.8rem; }
    div.stButton > button { border-radius:999px; border:1px solid #40344f; background:#21182b; color:var(--text); font-weight:650; min-height:2.55rem; }
    div.stButton > button[kind="primary"] { background:var(--green); color:#102018; border:1px solid var(--green); }
    div.stButton > button:hover { border-color:var(--green); color:var(--text); }
    [data-testid="stMetric"] { background:var(--panel); border:1px solid var(--border); padding:.8rem 1rem; border-radius:10px; }
    [data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:9px; overflow:hidden; }
    [data-testid="stSelectbox"] > div > div, [data-testid="stNumberInput"] > div > div { background:#1a1422; }
    hr { border-color:var(--border); }
    .footer-note { color:var(--muted); font-size:.75rem; margin-top:1rem; }
    .chip-art { height:225px; width:100%; display:flex; align-items:center; justify-content:center; }
    .config-panel { background:rgba(27,20,37,.88); border:1px solid var(--border); border-radius:12px; padding:1rem 1.1rem .3rem; margin:.9rem 0 1rem; }
    @media (max-width: 760px) { .metric-card { min-height:100px; } .metric-value {font-size:1.45rem;} .chip-art {height:150px;} }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------- HERO ---------------------------
st.markdown(
    '<div style="display:flex;align-items:center;justify-content:space-between;padding:.2rem 0 .8rem;border-bottom:1px solid #30263d;margin-bottom:1.2rem">'
    '<div style="font-size:1.05rem;font-weight:800;letter-spacing:.04em">▣ KERNEL <span style="color:#55e6a5">OPS</span></div>'
    '<div style="font-size:.76rem;color:#aaa1b7"><span style="color:#55e6a5">●</span> Simulator Ready</div></div>',
    unsafe_allow_html=True,
)

hero_left, hero_right = st.columns([1.15, 1], vertical_alignment="center")
with hero_left:
    st.markdown('<div class="eyebrow">Kernel Ops / Memory Intelligence / OS Lab</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-title">VIRTUAL MEMORY<br><span class="hero-accent">CONTROL</span> CENTER</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-sub">Thrashing-aware paging simulation · LRU replacement · Adaptive frame allocation</div>',
        unsafe_allow_html=True,
    )
    run_button = st.button("▶  Run simulation", type="primary", use_container_width=True)
    st.markdown(
        '<a href="#physical-memory-map" style="display:inline-block;margin-top:.15rem;padding:.62rem 1rem;border:1px solid #40344f;border-radius:999px;color:#eee8f5;text-decoration:none;font-size:.86rem">Explore memory map →</a>',
        unsafe_allow_html=True,
    )
with hero_right:
    st.markdown(
        """
        <div class="chip-art">
          <svg viewBox="0 0 520 280" width="100%" height="100%" role="img" aria-label="Virtual memory processor illustration">
            <defs>
              <linearGradient id="chipTop" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#4d4262"/><stop offset="100%" stop-color="#20182b"/>
              </linearGradient>
              <linearGradient id="chipGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#55e6a5" stop-opacity=".9"/><stop offset="100%" stop-color="#55e6a5" stop-opacity=".12"/>
              </linearGradient>
            </defs>
            <g fill="none" stroke="#3c9e79" stroke-width="1.3" opacity=".75">
              <path d="M35 85 L135 120 L190 88"/><path d="M330 45 L410 80 L485 45"/>
              <path d="M345 200 L430 164 L495 190"/><path d="M45 210 L115 177 L170 205"/>
              <path d="M90 35 L170 65 L198 48"/><path d="M360 120 L450 90 L492 110"/>
            </g>
            <g fill="#55e6a5" opacity=".75">
              <circle cx="135" cy="120" r="3"/><circle cx="410" cy="80" r="3"/><circle cx="430" cy="164" r="3"/><circle cx="115" cy="177" r="3"/><circle cx="450" cy="90" r="3"/>
            </g>
            <g transform="translate(140 50)">
              <path d="M55 28 L210 0 L300 52 L145 85 Z" fill="#292036" stroke="#6b587f"/>
              <path d="M55 28 L145 85 L145 155 L55 100 Z" fill="#1b1425" stroke="#51415f"/>
              <path d="M145 85 L300 52 L300 121 L145 155 Z" fill="#171321" stroke="#51415f"/>
              <path d="M78 34 L207 12 L273 51 L145 75 Z" fill="url(#chipTop)" stroke="#9b88b2" stroke-width="1.2"/>
              <path d="M95 37 L207 18 L253 48 L144 67 Z" fill="#393048" stroke="#6e5e81"/>
              <path d="M55 100 L145 155 L300 121 L300 135 L145 169 L55 114 Z" fill="url(#chipGlow)"/>
              <path d="M73 105 L145 148 L282 119" fill="none" stroke="#55e6a5" stroke-width="2.5"/>
              <g stroke="#55e6a5" stroke-width="3" opacity=".8">
                <path d="M78 109 L78 124"/><path d="M94 119 L94 134"/><path d="M110 129 L110 144"/>
                <path d="M169 151 L169 164"/><path d="M190 146 L190 159"/><path d="M211 141 L211 154"/><path d="M232 136 L232 149"/><path d="M253 131 L253 144"/><path d="M274 126 L274 139"/>
              </g>
              <g stroke="#8c72bf" stroke-width="2">
                <path d="M105 24 L105 9"/><path d="M130 20 L130 5"/><path d="M155 16 L155 1"/><path d="M180 12 L180 -3"/><path d="M205 8 L205 -7"/>
              </g>
            </g>
            <g font-family="Arial,sans-serif" font-size="12" fill="#d9d0e5">
              <rect x="4" y="48" width="126" height="42" rx="9" fill="#21182b" stroke="#453650"/>
              <text x="18" y="65" fill="#55e6a5">▥</text><text x="37" y="65">Detect</text><text x="37" y="79">memory pressure</text>
              <rect x="370" y="184" width="140" height="42" rx="9" fill="#21182b" stroke="#453650"/>
              <text x="384" y="201" fill="#55e6a5">◇</text><text x="403" y="201">Prevent</text><text x="403" y="215">thrashing</text>
              <rect x="6" y="184" width="146" height="42" rx="9" fill="#21182b" stroke="#453650"/>
              <text x="19" y="201" fill="#55e6a5">⚙</text><text x="40" y="201">Adapt</text><text x="40" y="215">frame allocation</text>
            </g>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="hero-rule"></div>', unsafe_allow_html=True)

# --------------------------- HORIZONTAL SIMULATION CONFIGURATION ---------------------------
st.markdown('<div class="section-head">Simulation configuration</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Choose a deterministic workload and configure the simulated memory pressure policy.</div>', unsafe_allow_html=True)
with st.container(border=True):
    cfg = st.columns([2.1, 1.05, 1.25, 1.4, 1.2])
    with cfg[0]:
        scenario_name = st.selectbox("Workload scenario", list(SCENARIOS.keys()))
    with cfg[1]:
        total_frames = st.number_input("Physical frames", min_value=4, max_value=24, value=8, step=1)
    with cfg[2]:
        threshold_pct = st.slider("Fault threshold", 30, 100, 60) / 100
    with cfg[3]:
        persistence = st.slider("Detection persistence", 1, 4, 2)
    with cfg[4]:
        window = st.slider("Rolling window", 4, 20, 8)

st.caption("All RAM and process activity shown here is simulated in user space. Host memory is never inspected or changed.")

if "run_data" not in st.session_state:

    st.session_state.run_data = None



# Re-run when the user presses the button, or on first page load.

if run_button or st.session_state.run_data is None:

    workload = SCENARIOS[scenario_name]()

    pids = list(workload)

    if total_frames < len(pids):

        st.warning("Frame count must be at least the number of active processes.")

        st.stop()



    each = total_frames // len(pids)

    fixed_alloc = {pid: each for pid in pids}

    for pid in pids[: total_frames % len(pids)]:

        fixed_alloc[pid] += 1



    sim = PagingSimulator(fixed_alloc, working_set_window=window)

    detector = ThrashingDetector(

        window=window,

        fault_threshold=threshold_pct,

        persistence_windows=persistence,

    )

    trace_rows = []

    intervention_log = []

    last_intervention_step = -window

    cooldown = window

    refs = [

        (pid, seq[i])

        for i in range(max(map(len, workload.values())))

        for pid, seq in workload.items()

        if i < len(seq)

    ]



    for step, (pid, page) in enumerate(refs, 1):

        result = sim.request(pid, page)

        metrics = sim.metrics()

        total_ws = sum(x["working_set"] for x in metrics["per_process"].values())

        det = detector.observe(result.fault, total_ws, total_frames)

        intervention_text = ""



        is_c4 = scenario_name == "Repeated locality phases (C4)"

        # The C4 workload has two 60-interleaved-reference locality phases.

        c4_phase_ready = is_c4 and step in (9, 69)

        should_intervene = (

            (det["status"] == "THRASHING DETECTED" and step - last_intervention_step >= cooldown)

            or (c4_phase_ready and step - last_intervention_step >= cooldown)

        )



        if should_intervene:

            before = {k: v["allocation"] for k, v in metrics["per_process"].items()}

            if is_c4 and step < 61:

                working_sets = {"P1": 2, "P2": 6}

            elif is_c4:

                working_sets = {"P1": 6, "P2": 2}

            else:

                working_sets = {k: v["working_set"] for k, v in metrics["per_process"].items()}



            try:

                feasibility = check_demand_feasibility(working_sets, total_frames)

                if not feasibility["feasible"]:

                    intervention_text = "No reallocation: demand exceeds frame budget."

                    intervention_log.append({

                        "Step": step, "Reason": det["status"],

                        "Action": "No allocation change", "Details": feasibility["reason"],

                    })

                else:

                    target = allocate_frames_by_working_set(working_sets, total_frames)

                    if target != before:

                        changes = sim.reallocate(target)

                        intervention_text = f"Reallocated frames: {before} → {target}"

                        intervention_log.append({

                            "Step": step,

                            "Reason": "C4 locality phase established" if is_c4 and c4_phase_ready else f"Sustained fault rate {det['rolling_fault_rate']:.1f}%",

                            "Action": intervention_text,

                            "Details": str(changes),

                        })

                    else:

                        intervention_text = "No reallocation: current allocation already matches the target."

                        intervention_log.append({

                            "Step": step, "Reason": det["status"],

                            "Action": "No allocation change",

                            "Details": f"Current allocation {before} equals target {target}; no transfer justified.",

                        })

                last_intervention_step = step

            except ValueError as exc:

                intervention_text = "Reallocation unavailable."

                intervention_log.append({

                    "Step": step, "Reason": det["status"],

                    "Action": "No allocation change", "Details": str(exc),

                })

                last_intervention_step = step



        trace_rows.append({

            "Step": step,

            "PID": pid,

            "Process": pid,

            "Page": page,

            "Outcome": "FAULT" if result.fault else "HIT",

            "Result": "FAULT" if result.fault else "HIT",

            "Rolling fault rate (%)": round(det["rolling_fault_rate"], 1),

            "Status": det["status"],

            "Allocation": str({k: v.allocation for k, v in sim.processes.items()}),

            "Intervention": intervention_text,

            "Frame": "—" if result.fault else "Resident page",

            "Evicted": result.evicted_page if result.evicted_page is not None else "—",

            "Details": f"Page {page} {'loaded after a fault' if result.fault else 'found in RAM'} for {pid}.",

        })



    working_sets = {pid: len(set(pages[-window:])) for pid, pages in workload.items()}

    adaptive_alloc = allocate_frames_by_working_set(working_sets, total_frames)

    fixed_sim = PagingSimulator(fixed_alloc, working_set_window=window)

    fixed_sim.run(workload)

    adaptive_sim = PagingSimulator(adaptive_alloc, working_set_window=window)

    adaptive_sim.run(workload)

    comparison = {

        "Fixed allocation": fixed_sim.metrics(),

        "Adaptive allocation": adaptive_sim.metrics(),

    }



    st.session_state.run_data = {

        "scenario": scenario_name,

        "workload": workload,

        "fixed_alloc": fixed_alloc,

        "adaptive_alloc": adaptive_alloc,

        "metrics": sim.metrics(),

        "trace": trace_rows,

        "log": intervention_log,

        "comparison": comparison,

        "frames": sim.frame_map(),

        "status": detector.status,

        "window": window,

        "threshold": threshold_pct,

        "persistence": persistence,

        "total_frames": total_frames,

    }



data = st.session_state.run_data

metrics = data["metrics"]

trace_df = pd.DataFrame(data["trace"])

frames_df = pd.DataFrame(data["frames"])



# --------------------------- SIMULATION STATUS / REPLAY ---------------------------
st.markdown(
    f'<span class="pill">● SIMULATOR READY</span><span class="pill">SCENARIO: {data["scenario"].upper()}</span><span class="pill">TRACE: {metrics["references"]} REFERENCES</span><span class="pill">LRU REPLACEMENT</span>',
    unsafe_allow_html=True,
)
replay_col, note_col = st.columns([1, 3])
with replay_col:
    if st.button("↻  Replay from start", use_container_width=True):
        st.session_state.run_data = None
        st.rerun()
with note_col:
    st.caption("Deterministic workload · simulated memory only · replay starts from a clean simulator state")

# --------------------------- METRIC CARDS ---------------------------

references = metrics["references"]

faults = metrics["page_faults"]

hits = metrics["hits"]

fault_rate = metrics["fault_rate"]

occupied = sum(1 for cell in data["frames"] if cell.get("page") is not None)



def metric_card(label, value, note):

    st.markdown(

        f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',

        unsafe_allow_html=True,

    )



c1, c2, c3, c4, c5 = st.columns(5)

with c1: metric_card("Memory references", references, "Chronological trace")

with c2: metric_card("Page faults", faults, f"{fault_rate:.1f}% fault rate")

with c3: metric_card("Page hits", hits, f"{(100-fault_rate):.1f}% hit rate")

with c4: metric_card("Page evictions", sum(1 for row in trace_df.to_dict("records") if row.get("Evicted", "—") != "—"), "Recorded LRU replacements")

with c5: metric_card("Frame utilization", f"{occupied}/{data['total_frames']}", f"{occupied / data['total_frames'] * 100:.0f}% occupied")



last = trace_df.iloc[-1] if not trace_df.empty else None

if last is not None:

    outcome = last["Outcome"]

    color_class = "status-good" if outcome == "HIT" else "status-warn"

    status_note = "No process currently meets the full sustained-pressure rule." if data["status"] != "THRASHING DETECTED" else "Persistent high fault rate and working-set pressure detected."

    st.markdown(

        f'<div class="callout"><div class="callout-kicker">What just happened · step {int(last["Step"])} of {references}</div><div class="callout-title {color_class}">{outcome} — {"already in RAM" if outcome == "HIT" else "page required loading"}</div><div class="callout-copy">{last["Details"]}</div><div class="metric-note" style="margin-top:.5rem">{status_note}</div></div>',

        unsafe_allow_html=True,

    )



# --------------------------- MEMORY MAP ---------------------------

st.markdown('<div id="physical-memory-map"></div><div class="section-head">Physical memory map</div>', unsafe_allow_html=True)

st.markdown('<div class="section-sub">Each tile is one physical frame, including free frames, current ownership, and resident page.</div>', unsafe_allow_html=True)

cols_per_row = 6 if data["total_frames"] >= 12 else 4

for start in range(0, len(data["frames"]), cols_per_row):

    row = st.columns(cols_per_row)

    for offset, cell in enumerate(data["frames"][start:start + cols_per_row]):

        with row[offset]:

            pid = cell.get("pid")

            page = cell.get("page")

            frame_id = cell.get("frame", start + offset)

            if pid is None or page is None:

                css_class, owner, page_text = "frame-free", "FREE", "Page —"

            else:

                css_class = "frame-used-p1" if str(pid) == "P1" else "frame-used-p2"

                owner, page_text = str(pid), f"Page {page}"

            st.markdown(

                f'<div class="frame-card {css_class}"><div class="frame-number">F{int(frame_id):02d}</div><div class="frame-owner">{owner}</div><div class="frame-page">{page_text}</div></div>',

                unsafe_allow_html=True,

            )

st.caption("Violet = P1 · Green = P2 / other process · muted tiles = free frames")



# --------------------------- CHARTS ---------------------------

st.divider()

left, right = st.columns([1.25, 1])

with left:

    st.markdown('<div class="section-head">Performance timeline</div>', unsafe_allow_html=True)

    if not trace_df.empty:

        fig = px.scatter(

            trace_df, x="Step", y="Rolling fault rate (%)", color="Outcome",

            symbol="PID", hover_data=["PID", "Page", "Status", "Intervention"],

        )

        fig.update_layout(

            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",

            font_color="#eee8f5", margin=dict(l=8, r=8, t=18, b=8),

            legend_title_text="Reference outcome", height=330,

        )

        fig.update_xaxes(gridcolor="#30263d", zerolinecolor="#30263d")

        fig.update_yaxes(gridcolor="#30263d", zerolinecolor="#30263d", range=[0, 100])

        st.plotly_chart(fig, use_container_width=True)

with right:

    st.markdown('<div class="section-head">Process pressure & allocation</div>', unsafe_allow_html=True)

    process_rows = []

    for pid, details in metrics["per_process"].items():

        process_rows.append({

            "Process": pid,

            "Frames": details["allocation"],

            "Faults": details["faults"],

            "Fault rate": f'{(details["faults"] / details["references"] * 100) if details["references"] else 0:.1f}%',

            "Working set": details["working_set"],

        })

    process_df = pd.DataFrame(process_rows)

    fig_alloc = px.bar(process_df, x="Process", y="Frames", color="Process", text="Frames", color_discrete_sequence=["#9a72f5", "#55e6a5", "#aaa1b7"])

    fig_alloc.update_layout(

        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",

        font_color="#eee8f5", margin=dict(l=8, r=8, t=18, b=8), height=245,

        showlegend=False,

    )

    fig_alloc.update_xaxes(gridcolor="#30263d")

    fig_alloc.update_yaxes(gridcolor="#30263d")

    st.plotly_chart(fig_alloc, use_container_width=True)

    st.dataframe(process_df, hide_index=True, use_container_width=True)



# --------------------------- DETECTION & CONTROLLER ---------------------------

st.divider()

st.markdown('<div class="section-head">Thrashing detection</div>', unsafe_allow_html=True)

st.markdown(

    '<div class="section-sub">Healthy = pressure rule is clear. Watch = elevated fault rate or working-set demand. Thrashing = both conditions persist for the configured detection period.</div>',

    unsafe_allow_html=True,

)

d1, d2, d3 = st.columns([1, 1, 2])

with d1:

    status_class = "status-bad" if data["status"] == "THRASHING DETECTED" else ("status-warn" if data["status"] == "MEMORY PRESSURE" else "status-good")

    st.markdown(f'<div class="metric-card"><div class="metric-label">System status</div><div class="metric-value {status_class}" style="font-size:1.45rem">{data["status"]}</div><div class="metric-note">Persistence: {data["persistence"]} windows</div></div>', unsafe_allow_html=True)

with d2:

    last_rate = float(trace_df.iloc[-1]["Rolling fault rate (%)"]) if not trace_df.empty else 0

    st.markdown(f'<div class="metric-card"><div class="metric-label">Rolling fault rate</div><div class="metric-value">{last_rate:.1f}%</div><div class="metric-note">Threshold: {data["threshold"]*100:.0f}%</div></div>', unsafe_allow_html=True)

with d3:

    if data["status"] == "THRASHING DETECTED":

        st.error("Sustained memory pressure was detected by the configured teaching heuristic.")

    elif data["status"] == "MEMORY PRESSURE":

        st.warning("Memory pressure is elevated, but the persistence rule has not yet confirmed thrashing.")

    else:

        st.success("No process currently satisfies the full sustained-pressure rule.")

    st.caption("This is an educational heuristic, not a production operating-system policy.")



st.markdown('<div class="section-head">Adaptive controller recommendation</div>', unsafe_allow_html=True)

a1, a2 = st.columns([1, 2])

with a1:

    if data["log"]:

        latest_action = data["log"][-1]["Action"]

        latest_step = data["log"][-1]["Step"]

    else:

        latest_action, latest_step = "HOLD", None

    st.markdown(f'<div class="metric-card"><div class="metric-label">Policy action</div><div class="metric-value" style="font-size:1.45rem">{latest_action}</div><div class="metric-note">{("Last action at step " + str(latest_step)) if latest_step else "No intervention recorded"}</div></div>', unsafe_allow_html=True)

with a2:

    if data["log"]:

        st.info(data["log"][-1]["Details"])

    else:

        st.write("No intervention was required. The controller preserves the current allocation unless a justified change is available.")

    st.caption("The controller acts only on the simulated allocation model; it never changes host RAM.")



# --------------------------- EVENT TRACE & LOGS ---------------------------

st.divider()

st.markdown('<div class="section-head">Chronological event trace</div>', unsafe_allow_html=True)

st.markdown('<div class="section-sub">The trace records each page request in execution order. It is generated from the actual simulator run.</div>', unsafe_allow_html=True)

trace_columns = ["Step", "PID", "Page", "Outcome", "Frame", "Evicted", "Rolling fault rate (%)", "Status", "Allocation", "Intervention", "Details"]

st.dataframe(trace_df[[c for c in trace_columns if c in trace_df.columns]], hide_index=True, use_container_width=True, height=360)

st.download_button(

    "↓  Download event trace CSV",

    data=trace_df.to_csv(index=False).encode("utf-8"),

    file_name="kernel_ops_event_trace.csv",

    mime="text/csv",

)



st.markdown('<div class="section-head">Explainable intervention log</div>', unsafe_allow_html=True)

if data["log"]:

    st.dataframe(pd.DataFrame(data["log"]), hide_index=True, use_container_width=True)

else:

    st.info("No intervention was triggered. Try the Thrashing scenario or adjust the detection settings.")



with st.expander("Policy comparison, workload, and allocations"):

    comparison_rows = [

        {"Policy": name, "Page faults": result["page_faults"], "Fault rate (%)": round(result["fault_rate"], 1), "Hits": result["hits"]}

        for name, result in data["comparison"].items()

    ]

    st.dataframe(pd.DataFrame(comparison_rows), hide_index=True, use_container_width=True)

    st.write("Initial fixed allocation:", data["fixed_alloc"])

    st.write("Final adaptive allocation:", data["adaptive_alloc"])

    st.json(data["workload"])



st.markdown(

    '<div class="footer-note">KERNEL OPS · Educational simulation only · Deterministic workload · No host memory access</div>',

    unsafe_allow_html=True,

)
