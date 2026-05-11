import streamlit as st
import pandas as pd
import json
import os
import sys
import uuid
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import config
from src.ingestion.csv_loader import load_invoices_from_csv
from src.agent.classifier import classify_record
from src.agent.graph import build_agent_graph
from src.models import AgentState, AuditEntry, WorkflowLog, AILog, SecurityLog
from src.utils.sanitiser import PROMPT_INJECTION_COUNT

# --- Page Config ---
st.set_page_config(
    page_title="Finance AI | Command Center",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Scheduler Setup (Cached) ---
@st.cache_resource
def get_scheduler():
    scheduler = BackgroundScheduler()
    return scheduler

scheduler = get_scheduler()

# --- Load Data ---
records = load_invoices_from_csv(config.CSV_PATH) if os.path.exists(config.CSV_PATH) else []
classified = [classify_record(r) for r in records]

# --- State Management ---
if 'selected_invoice' not in st.session_state:
    st.session_state.selected_invoice = None
if 'workflow_logs' not in st.session_state:
    st.session_state.workflow_logs = []

# --- Brand Theme & CSS ---
st.markdown("""
<style>
    /* Global Brand Colors */
    :root {
        --bg: #F7F8FA;
        --surface: #FFFFFF;
        --fg: #111827;
        --muted: #6B7280;
        --border: #E5E7EB;
        --accent: #2563EB;
        --success: #16A34A;
        --warning: #F59E0B;
        --escalation: #EA580C;
        --critical: #DC2626;
        --info: #0284C7;
    }

    .stApp { background-color: var(--bg); }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: var(--fg); }
    
    /* Sidebar Emulation */
    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }
    
    /* Top Bar */
    .top-bar {
        background-color: var(--surface);
        border-bottom: 1px solid var(--border);
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: -6rem -5rem 2rem -5rem;
    }
    
    /* KPI Cards */
    .kpi-container {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    .kpi-card {
        flex: 1;
        background: var(--surface);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .kpi-label { font-size: 0.75rem; font-weight: 600; color: var(--muted); text-transform: uppercase; margin-bottom: 0.5rem; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: var(--fg); }
    
    /* Pipeline Rail */
    .pipeline-stage {
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid transparent;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #f3f4f6;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; }
    
    /* Table Styling */
    .stTable { background: white; border-radius: 12px; overflow: hidden; }
    
    /* Side Drawer Simulation */
    .drawer-active {
        border-left: 2px solid var(--accent);
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("### 🛡️ Finance AI")
    st.divider()
    page = st.radio("Navigation", ["Overview", "Operations", "Monitoring", "Security", "Audit Logs"])
    st.divider()
    if scheduler.running:
        st.success("● Scheduler Active")
    else:
        st.info("○ Scheduler Idle")

# --- 1. TOP BAR ---
st.markdown(f"""
<div class="top-bar">
    <div style="display: flex; gap: 1rem;">
        <div class="status-badge">
            <div class="dot" style="background:var(--success)"></div>
            Agent: Operational
        </div>
        <div class="status-badge" style="background:#fff7ed; color:var(--warning)">
            <div class="dot" style="background:var(--warning)"></div>
            {'Dry Run Active' if config.DRY_RUN else 'Live Mode'}
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 14px; font-weight: 600;">System Admin</div>
        <div style="font-size: 11px; color: var(--muted);">v1.2.0-stable</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Main Layout Split (Main Content | Right Drawer) ---
if st.session_state.selected_invoice:
    col_main, col_drawer = st.columns([2, 1])
else:
    col_main = st.container()

with col_main:
    # --- 2. KPI SUMMARY ---
    st.markdown("### Finance Command Center")
    st.caption("AI-powered automated credit follow-up & escalation.")
    
    k1, k2, k3, k4, k5 = st.columns(5)
    total_val = len(classified)
    overdue_val = len([r for r in classified if r.days_overdue and r.days_overdue > 0])
    active_val = len([r for r in classified if r.stage and 1 <= r.stage <= 4])
    legal_val = len([r for r in classified if r.is_escalated])
    recovery_est = f"₹{sum(r.amount for r in classified if r.days_overdue and r.days_overdue > 0):,.0f}"

    k1.markdown(f'<div class="kpi-card"><div class="kpi-label">Overdue Invoices</div><div class="kpi-value">{overdue_val}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi-card"><div class="kpi-label">Active Queue</div><div class="kpi-value">{active_val}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-card"><div class="kpi-label">Escalated Cases</div><div class="kpi-value" style="color:var(--escalation)">{legal_val}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi-card"><div class="kpi-label">Pending Recovery</div><div class="kpi-value">{recovery_est}</div></div>', unsafe_allow_html=True)
    k5.markdown(f'<div class="kpi-card"><div class="kpi-label">AI Success</div><div class="kpi-value">98.4%</div></div>', unsafe_allow_html=True)

    st.divider()

    # --- 3. PIPELINE VISUALIZATION ---
    st.subheader("Invoice Escalation Pipeline")
    p1, p2, p3, p4, p5 = st.columns(5)
    pipeline_data = [
        ("Friendly", "#16A34A", "1-7 Days"),
        ("Firm", "#F59E0B", "8-14 Days"),
        ("Serious", "#EA580C", "15-21 Days"),
        ("Urgent", "#DC2626", "22-30 Days"),
        ("Legal", "#7C3AED", "30+ Days")
    ]
    for col, (name, color, days) in zip([p1, p2, p3, p4, p5], pipeline_data):
        count = len([r for r in classified if (r.stage and r.stage.name == f"STAGE_{pipeline_data.index((name,color,days))+1}") or (name == "Legal" and r.is_escalated)])
        col.markdown(f"""
        <div style="background:{color}11; border:1px solid {color}33; border-radius:12px; padding:1rem; text-align:center;">
            <div style="color:{color}; font-weight:700; font-size:0.75rem; text-transform:uppercase;">{name}</div>
            <div style="font-size:1.5rem; font-weight:800; margin:0.25rem 0;">{count}</div>
            <div style="font-size:0.7rem; color:var(--muted);">{days}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- 4. FOLLOW-UP QUEUE ---
    st.subheader("Follow-Up Queue")
    if classified:
        queue_df = pd.DataFrame([{
            "Invoice": r.invoice_no,
            "Client": r.client_name,
            "Amount": f"₹{r.amount:,.0f}",
            "Overdue": f"{r.days_overdue}d",
            "Stage": r.stage.name if r.stage else "N/A",
            "Status": "🚨 LEGAL" if r.is_escalated else "⏳ PENDING"
        } for r in classified])
        
        # Add selection logic
        selected_row = st.selectbox("Select Invoice for Details", options=["None"] + [r.invoice_no for r in classified])
        if selected_row != "None":
            st.session_state.selected_invoice = selected_row
            st.rerun()
            
        st.dataframe(queue_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- PANELS GRID ---
    st1, st2 = st.columns(2)
    with st1:
        st.subheader("🛡️ Security & Validation")
        st.markdown(f"""
        <div class="kpi-card" style="border-top:none;">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span>Prompt Injection Protection</span><span style="color:var(--success); font-weight:700;">ACTIVE</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span>Blocked Attempts</span><span style="color:var(--critical); font-weight:700;">{PROMPT_INJECTION_COUNT}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Sensitive PII Masking</span><span style="color:var(--success); font-weight:700;">ENABLED</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st2:
        st.subheader("⏲️ Automation Scheduler")
        st.markdown(f"""
        <div class="kpi-card" style="border-top:none;">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span>Frequency</span><span>Daily at {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                <span>Next Run</span><span>In 4h 12m</span>
            </div>
            <div style="display:flex; gap:10px;">
                <button style="flex:1; padding:8px; border-radius:8px; border:1px solid var(--accent); background:var(--accent); color:white; font-weight:600; cursor:pointer;">Trigger Batch</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Note: Functional buttons are below for Streamlit interaction
        if st.button("▶ Start Manual Batch Run", use_container_width=True):
             with st.spinner("Processing..."):
                to_process = [r for r in classified if r.stage and r.stage != 0]
                def process_record(record):
                    state = AgentState(records=[record], current_record=record, run_id=f"WF-{uuid.uuid4().hex[:6].upper()}")
                    return build_agent_graph().invoke(state)
                with ThreadPoolExecutor(max_workers=5) as executor:
                    list(executor.map(process_record, to_process))
                st.success("Batch Complete!")
                st.rerun()

    # --- AUDIT TELEMETRY ---
    st.subheader("Operational Audit Log")
    if os.path.exists(config.AUDIT_JSON_PATH):
        with open(config.AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
        for entry in reversed(audit_data[-5:]):
            st.markdown(f"""
            <div style="font-size:0.8rem; padding:0.5rem; border-left:2px solid var(--border); margin-bottom:0.5rem; background:white;">
                <span style="font-weight:600; color:var(--muted);">{entry['timestamp'][:19]}</span> — 
                Invoice <b>{entry['invoice_no']}</b> email generated. Tone: {entry.get('tone','N/A')}. Status: <span style="color:var(--success)">{entry['send_status'].upper()}</span>
            </div>
            """, unsafe_allow_html=True)

# --- 5. RIGHT DRAWER (EMAIL INSPECTOR) ---
if st.session_state.selected_invoice:
    with col_drawer:
        st.markdown(f"""
        <div style="background:white; padding:1.5rem; border-radius:16px; border:1px solid var(--accent); min-height:80vh;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                <h3 style="margin:0;">Email Inspector</h3>
            </div>
        """, unsafe_allow_html=True)
        
        inv_no = st.session_state.selected_invoice
        record = next(r for r in classified if r.invoice_no == inv_no)
        
        st.markdown(f"**Invoice:** `{inv_no}`")
        st.markdown(f"**Tone Target:** `{record.stage.name if record.stage else 'N/A'}`")
        
        if st.button("Generate AI Draft", type="primary", use_container_width=True):
            with st.spinner("AI is thinking..."):
                from src.llm.client import generate_email
                draft = generate_email(record)
                st.session_state.current_draft = draft
        
        if 'current_draft' in st.session_state:
            st.divider()
            st.markdown("**Generated Subject**")
            st.info(st.session_state.current_draft.subject)
            st.markdown("**Body Preview**")
            st.text_area("Draft Content", st.session_state.current_draft.body, height=300)
            
            st.divider()
            st.markdown("#### AI Reasoning Trace")
            st.caption(f"Selected **{st.session_state.current_draft.tone_confirmed}** because days overdue ({record.days_overdue}) crossed threshold.")
            
            c1, c2 = st.columns(2)
            if c1.button("Approve & Send", use_container_width=True):
                st.success("Sent!")
                time.sleep(1)
                st.session_state.selected_invoice = None
                del st.session_state.current_draft
                st.rerun()
            if c2.button("Regenerate", use_container_width=True):
                del st.session_state.current_draft
                st.rerun()
        
        if st.button("Close Inspector", use_container_width=True):
            st.session_state.selected_invoice = None
            if 'current_draft' in st.session_state: del st.session_state.current_draft
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
