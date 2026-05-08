import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import tempfile
from pathlib import Path
from pyvis.network import Network
import streamlit.components.v1 as components
import time

BACKEND = "http://localhost:8888"

st.set_page_config(page_title="SBOM 核心控制台", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# ── Auth Firewall ──────────────────────────────────────────────
_CRED_USER = "moBS"
_CRED_PASS = "dfahjeaiwf23878@#"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
    <div style="display:flex; justify-content:center; align-items:center; min-height:60vh;">
        <div style="text-align:center;">
            <h1>🛡️ SBOM 核心控制台</h1>
            <p style="color:#8B949E;">身份验证</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        user = st.text_input("用户名")
        pwd = st.text_input("密码", type="password")
        submitted = st.form_submit_button("登录", use_container_width=True)
        if submitted:
            if user == _CRED_USER and pwd == _CRED_PASS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("凭证无效，请重试。")
    st.stop()

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #C9D1D9; }
    .hc { background: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 14px 16px; }
    .terminal-window { background: #010409; border: 1px solid #30363D; border-radius: 6px; padding: 12px; font-family: monospace; color: #7EE787; font-size: 0.8rem; max-height: 180px; overflow-y: auto; }
    h3 { margin-top: 0 !important; }
</style>
""", unsafe_allow_html=True)

def api_get(path):
    try:
        r = requests.get(f"{BACKEND}{path}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def api_post(path, body):
    return requests.post(f"{BACKEND}{path}", json=body, timeout=600)

# ── Sidebar: Scan Control ──────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛠️ 扫描中控台")
    scan_target = st.text_input("探测目标", placeholder="/home/ubuntu/vuln-target")

    if st.button("启动扫描", use_container_width=True, type="primary"):
        if scan_target:
            progress = st.empty()
            log_area = st.empty()
            steps = ["INIT", "SBOM", "CVE", "SAST", "FIN"]
            logs = [f"REQ: {scan_target}"]

            for i, step in enumerate(steps[:-1]):
                step_html = " | ".join([
                    '<span style="color:{}">{}</span>'.format("#58A6FF" if j==i else "#484F58", s)
                    for j, s in enumerate(steps)
                ])
                progress.markdown(f"**PHASE**: {step_html}", unsafe_allow_html=True)
                logs.append(f"EXEC: {step}")
                html = "".join([
                    '<div><span style="color:#8B949E">[{}]</span> {}</div>'.format(time.strftime("%H:%M:%S"), l)
                    for l in logs[-6:]
                ])
                log_area.markdown('<div class="terminal-window">{}</div>'.format(html), unsafe_allow_html=True)
                time.sleep(0.3)

            try:
                r = api_post("/api/scan", {"path": scan_target})
                if r.status_code == 200:
                    st.success("DONE")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("ERR: {}".format(r.json().get('detail', r.text[:200])))
            except Exception as e:
                st.error(str(e))

# ── Load history index ─────────────────────────────────────────
history_data = api_get("/api/history")
history = history_data.get("reports", []) if history_data else []

st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #30363D; padding-bottom:10px; margin-bottom:16px;">
    <h2 style="margin:0;">🛡️ SBOM 核心控制台</h2>
    <div style="font-size:0.8rem; color:#7EE787; border:1px solid #238636; padding:2px 10px; border-radius:4px;">LIVE</div>
</div>
""", unsafe_allow_html=True)

if not history:
    st.info("无扫描记录。请在左侧输入目标并启动扫描。")
    st.stop()

# ── Global report selector (drives the entire page) ────────────
report_labels = ["{}  |  {}".format(r['report_id'], r['target']) for r in history]

if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0

selected_idx = st.selectbox(
    "当前报告 (切换后全页面数据同步刷新)",
    range(len(report_labels)),
    format_func=lambda i: report_labels[i],
    index=st.session_state.selected_idx,
    key="report_selector",
)
st.session_state.selected_idx = selected_idx
chosen_id = history[selected_idx]["report_id"]

# ── Fetch the FULL report from backend (single source of truth) ─
report = api_get("/api/history/{}".format(chosen_id))

if not report:
    st.error("无法加载报告: {}".format(chosen_id))
    st.stop()

# ── All metrics derived from report object ONLY ────────────────
scan_info = report.get("scan_info", {})
vuln_summary = report.get("vulnerabilities", {}).get("summary", {})
vuln_details = report.get("vulnerabilities", {}).get("details", [])
static_findings = report.get("static_analysis", [])
policy = report.get("policy", {})

files_scanned = scan_info.get("files_scanned", 0)
component_count = scan_info.get("component_count", 0)
vuln_count = vuln_summary.get("total", 0)
sast_count = len(static_findings)

# ── Metric Cards ───────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("<div class='hc'><small>FILES_SCANNED</small><h3>{}</h3></div>".format(files_scanned), unsafe_allow_html=True)
with c2:
    st.markdown("<div class='hc'><small>COMPONENTS</small><h3>{}</h3></div>".format(component_count), unsafe_allow_html=True)
with c3:
    st.markdown("<div class='hc'><small>CVE_COUNT</small><h3 style='color:#F85149'>{}</h3></div>".format(vuln_count), unsafe_allow_html=True)
with c4:
    st.markdown("<div class='hc'><small>SAST_HITS</small><h3>{}</h3></div>".format(sast_count), unsafe_allow_html=True)

# ── Tabs (all bound to report) ────────────────────────────────
tab_sbom, tab_cve, tab_sast, tab_graph, tab_hist = st.tabs([
    "1.资产透视(SBOM)", "2.风险匹配(CVE)", "3.源码审计(SAST)",
    "4.依赖拓扑(Graph)", "5.实验记录(History)"
])

# ── Tab 1: SBOM ───────────────────────────────────────────────
with tab_sbom:
    st.markdown("**TARGET**: `{}`  |  **TIME**: `{}`  |  **DURATION**: `{}s`".format(
        report.get('target'), report.get('scanned_at'), report.get('duration_seconds')))
    col_l, col_r = st.columns([2, 1])
    with col_l:
        if vuln_details:
            df = pd.DataFrame(vuln_details)[["component", "version", "severity"]].drop_duplicates()
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Syft 未提取到带版本号的组件。确认目标含 requirements.txt 等清单。")
    with col_r:
        status = policy.get("status", "UNKNOWN")
        color = "#238636" if status == "PASS" else "#F85149"
        reasons_html = "".join(["<div>• {}</div>".format(r) for r in policy.get("reasons", [])])
        st.markdown("""
        <div style="border:1px solid {}; padding:20px; border-radius:6px; text-align:center;">
            <h2 style="color:{}; margin:0;">{}</h2>
            <p style="color:#8B949E; margin:5px 0;">POLICY_GATE</p>
            <div style="text-align:left; font-size:0.8rem; margin-top:10px;">{}</div>
        </div>
        """.format(color, color, status, reasons_html), unsafe_allow_html=True)

# ── Tab 2: CVE ────────────────────────────────────────────────
with tab_cve:
    if not vuln_details:
        st.success("NO_CVE_FOUND")
    else:
        for v in vuln_details:
            with st.expander("[{}] {} | {} @ {}".format(v['severity'], v['cve_id'], v['component'], v['version'])):
                st.markdown("**DESC**: {}".format(v.get('description')))
                st.markdown("**CVSS**: `{}` | **VECTOR**: `{}` | **SOURCE**: `{}`".format(
                    v.get('cvss_score', 'N/A'), v.get('cvss_vector', 'N/A'), v.get('source', 'N/A')))
                fix_str = ', '.join(v.get('fix_versions') or ['NONE'])
                st.markdown("**FIX**: `{}`".format(fix_str))
                if v.get("ai_fix"):
                    st.info(v["ai_fix"])

# ── Tab 3: SAST ───────────────────────────────────────────────
with tab_sast:
    if not static_findings:
        st.success("SAST: 0 findings")
    else:
        for finding in static_findings:
            with st.expander("{} | {}:{} | {}".format(
                finding.get('severity','?'), finding['file'], finding['line'], finding['rule_id'])):
                st.code(finding["content"], language="python")
                st.markdown("**MSG**: {}".format(finding['message']))
                if finding.get("ai_fix"):
                    st.info(finding["ai_fix"])

# ── Tab 4: Graph ──────────────────────────────────────────────
with tab_graph:
    net = Network(height="480px", width="100%", bgcolor="transparent", font_color="#C9D1D9", directed=True)
    net.add_node("root", label="TARGET", color="#58A6FF", size=22)
    seen = set()
    for v in vuln_details[:50]:
        name = v["component"]
        if name in seen:
            continue
        seen.add(name)
        if v["severity"] in ("CRITICAL", "HIGH"):
            ncolor = "#F85149"
        elif v["severity"] == "MEDIUM":
            ncolor = "#D29922"
        else:
            ncolor = "#30363D"
        net.add_node(name, label=name, color=ncolor, size=14)
        net.add_edge("root", name, color="#21262D", width=0.5)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        components.html(Path(tmp.name).read_text(), height=520)

# ── Tab 5: History (context switching) ────────────────────────
with tab_hist:
    st.caption("在页面顶部的下拉框中切换报告，全页面数据将同步刷新。")
    if history:
        df_h = pd.DataFrame(history)
        col_order = ["report_id", "target", "scanned_at", "policy_status",
                      "files_scanned", "component_count", "total_vulns",
                      "critical", "high"]
        existing = [c for c in col_order if c in df_h.columns]
        st.dataframe(df_h[existing], use_container_width=True, hide_index=True)
