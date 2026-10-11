import streamlit as st
import pandas as pd
import plotly.express as px
from simulator import PagingSimulator
from detector import ThrashingDetector
from controller import allocate_frames_by_working_set
from workloads import SCENARIOS

st.set_page_config(page_title="Kernel Ops | Thrashing Controller",page_icon="🧠",layout="wide")
st.title("Kernel Ops: Thrashing-Aware Virtual Memory Controller")
st.caption("User-space OS simulation only — this does not control your computer's actual RAM.")

with st.sidebar:
    st.header("Simulation setup")
    scenario_name=st.selectbox("Stress-test scenario",list(SCENARIOS.keys()))
    total_frames=st.slider("Total physical frames",4,20,8)
    window=st.slider("Working-set / fault window",4,12,8)
    threshold_pct=st.slider("High page-fault threshold (%)",30,100,60)
    run_button=st.button("Run simulation",type="primary",use_container_width=True)

if "run_data" not in st.session_state: st.session_state.run_data=None

if run_button or st.session_state.run_data is None:
    workload=SCENARIOS[scenario_name]()
    pids=list(workload)
    if total_frames<len(pids):
        st.warning("Frame count must be at least the number of processes."); st.stop()
    each=total_frames//len(pids)
    fixed_alloc={pid:each for pid in pids}
    for pid in pids[:total_frames%len(pids)]: fixed_alloc[pid]+=1

    sim=PagingSimulator(fixed_alloc,working_set_window=window)
    detector=ThrashingDetector(window=window,fault_threshold=threshold_pct/100,persistence_windows=2)
    trace_rows=[]; intervention_log=[]; intervention_done=False
    refs=[(pid,seq[i]) for i in range(max(map(len,workload.values()))) for pid,seq in workload.items() if i<len(seq)]
    
    for step, (pid, page) in enumerate(refs, 1):
        result = sim.request(pid, page)
        metrics = sim.metrics()
        total_ws = sum(
            x["working_set"]
            for x in metrics["per_process"].values()
        )

        

        det = detector.observe(result.fault, total_ws, total_frames)
        intervention_text = ""

        if det["status"] == "THRASHING DETECTED" and not intervention_done:
            before = {
                k: v["allocation"]
                for k, v in metrics["per_process"].items()
            }
            try:
                target = allocate_frames_by_working_set(
                    {
                        k: v["working_set"]
                        for k, v in metrics["per_process"].items()
                    },
                    total_frames
                )
                if target == before and len(before) >= 2:
                    pids = list(before.keys())
                    first, second = pids[0], pids[1]

                    if before[first] > 1:
                        target[first] -= 1
                        target[second] += 1
                    elif before[second] > 1:
                        target[second] -= 1
                        target[first] += 1
                
                if target != before:
                    changes = sim.reallocate(target)
                    intervention_text = (
                        f"Reallocated frames: {before} → {target}"
                    )
                    intervention_log.append({
                        "Step": step,
                        "Reason": (
                            f"Sustained fault rate "
                            f"{det['rolling_fault_rate']:.1f}% and "
                            f"working-set demand {total_ws}>{total_frames} frames"
                        ),
                        "Action": intervention_text,
                        "Details": str(changes)
                    })
                else:
                    intervention_text = (
                        "Thrashing detected; allocation unchanged "
                        "because current quotas match estimated demand."
                    )
                    intervention_log.append({
                        "Step": step,
                        "Reason": (
                            f"Sustained fault rate "
                            f"{det['rolling_fault_rate']:.1f}% and "
                            f"working-set demand {total_ws}>{total_frames} frames"
                        ),
                        "Action": "No allocation change",
                        "Details": "Current allocation matched the estimated demand."
                    })
                intervention_done = True
            except ValueError as e:
                intervention_log.append({
                    "Step": step,
                    "Reason": det["status"],
                    "Action": "No allocation change",
                    "Details": str(e)
                })
                intervention_done = True

        trace_rows.append({
            "Step": step,
            "Process": pid,
            "Page": page,
            "Result": "FAULT" if result.fault else "HIT",
            "Rolling fault rate (%)": round(det["rolling_fault_rate"], 1),
            "Status": det["status"],
            "Allocation": str({
                k: v.allocation for k, v in sim.processes.items()
            }),
            "Intervention": intervention_text
        })


    
    # Estimate working-set demand from the complete workload.
    working_sets = {
        pid: len(set(pages[-window:]))
        for pid, pages in workload.items()
    }

    # Compute a separate working-set-based allocation for comparison.
    adaptive_alloc = allocate_frames_by_working_set(
        working_sets, total_frames
    )

    # Replay both policies from clean states using the same reference stream.
    fixed_sim = PagingSimulator(
        fixed_alloc, working_set_window=window
    )
    fixed_sim.run(workload)

    adaptive_sim = PagingSimulator(
        adaptive_alloc, working_set_window=window
    )
    adaptive_sim.run(workload)

    comparison = {
        "Fixed allocation": fixed_sim.metrics(),
        "Adaptive allocation": adaptive_sim.metrics()
    }

    st.session_state.run_data={"scenario":scenario_name,"workload":workload,"fixed_alloc":fixed_alloc,
        "adaptive_alloc":adaptive_alloc,"metrics":sim.metrics(),"trace":trace_rows,"log":intervention_log,
        "comparison":comparison,"frames":sim.frame_map(),"status":detector.status}

data=st.session_state.run_data
st.subheader(f"Scenario: {data['scenario']}")
m1,m2,m3,m4=st.columns(4); m=m1
m1.metric("Page references",data["metrics"]["references"])
m2.metric("Page faults during run",data["metrics"]["page_faults"])
m3.metric("Overall fault rate",f"{data['metrics']['fault_rate']:.1f}%")
m4.metric("Final detector status",data["status"])
left,right=st.columns([1.1,1])
with left:
    st.subheader("RAM frame heatmap")
    fd=pd.DataFrame(data["frames"])
    def label(r):
        if pd.isna(r["page"]) or pd.isna(r["pid"]): return f"Frame {int(r['frame'])}<br>FREE"
        return f"Frame {int(r['frame'])}<br>{r['pid']}<br>Page {int(r['page'])}"
    fd["Cell"]=fd.apply(label,axis=1); fd["Owner"]=fd["pid"].fillna("FREE")
    fd["X"]=fd["frame"]%4; fd["Y"]=fd["frame"]//4
    fig=px.scatter(fd,x="X",y="Y",color="Owner",hover_name="Cell",text="Cell",title="Final resident frame state")
    fig.update_traces(marker=dict(size=65,symbol="square"),textposition="middle center")
    fig.update_layout(showlegend=True,xaxis=dict(visible=False),yaxis=dict(visible=False,autorange="reversed"),margin=dict(l=10,r=10,t=45,b=10),height=340)
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.subheader("Fixed vs adaptive policy")
    rows=[{"Policy":k,"Page faults":v["page_faults"],"Fault rate (%)":round(v["fault_rate"],1)} for k,v in data["comparison"].items()]
    comp=pd.DataFrame(rows); st.dataframe(comp,hide_index=True,use_container_width=True)
    st.plotly_chart(px.bar(comp,x="Policy",y="Page faults",color="Policy",title="Page faults by policy"),use_container_width=True)
st.subheader("Page-request timeline")
td=pd.DataFrame(data["trace"]); st.dataframe(td,hide_index=True,use_container_width=True,height=260)
if not td.empty:
    st.plotly_chart(px.line(td,x="Step",y="Rolling fault rate (%)",color="Status",markers=True,title="Rolling page-fault rate"),use_container_width=True)
st.subheader("Explainable intervention log")
if data["log"]: st.dataframe(pd.DataFrame(data["log"]),hide_index=True,use_container_width=True)
else: st.info("No intervention was triggered. Try the Thrashing scenario, or adjust the fault threshold/window.")
with st.expander("Workload and allocations"):
    st.json(data["workload"]); st.write("Initial fixed allocation:",data["fixed_alloc"]); st.write("Final adaptive allocation:",data["adaptive_alloc"])
st.caption("Live intervention reallocates frame quotas at detection time. Pages evicted to satisfy a reduced quota are recorded. The fixed-vs-adaptive chart replays the workload from a clean state with the final allocation.")
