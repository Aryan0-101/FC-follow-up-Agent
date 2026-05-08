import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime


# Add project root to sys.path to resolve 'src' imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import config
from src.ingestion.csv_loader import load_invoices_from_csv
from src.agent.classifier import classify_record
from src.agent.graph import build_agent_graph
from src.models import AgentState
import uuid
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="Finance Email Agent",
    page_icon="📧",
    layout="wide"
)

# --- Custom CSS for Gamified UI ---
st.markdown("""
<style>
    :root {
        --bg: #0f1117;
        --surface: #1a1d27;
        --accent: #6c63ff;
        --accent2: #00d4aa;
        --warn: #f59e0b;
        --danger: #ef4444;
        --success: #22c55e;
        --legal: #a855f7;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: var(--surface);
        border: 1px solid #2e3250;
        border-radius: 12px;
        padding: 1.2rem;
        border-top: 4px solid var(--accent);
        transition: transform .2s;
    }
    .kpi-card:hover { transform: translateY(-3px); border-color: var(--accent); }
    .kpi-val { font-size: 2rem; font-weight: 800; margin-bottom: 0; }
    .kpi-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    
    /* Stage Tracker */
    .stage-rail {
        display: flex;
        gap: 10px;
        margin-bottom: 2rem;
    }
    .stage-item {
        flex: 1;
        padding: 1rem;
        background: rgba(26, 29, 39, 0.6);
        border: 1px solid #2e3250;
        border-radius: 10px;
        text-align: center;
        transition: all 0.3s;
    }
    .stage-item.active { border-color: var(--accent); background: rgba(108, 99, 255, 0.1); box-shadow: 0 0 15px rgba(108, 99, 255, 0.2); }
    .stage-dot { width: 10px; height: 10px; border-radius: 50%; margin: 0 auto 10px; }
    
    /* Badges */
    .stBadge { padding: 0.2rem 0.6rem; border-radius: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
col_title, col_mode = st.columns([3, 1])
with col_title:
    st.title("📧 Finance Email Agent")
    st.caption(f"Intelligent Credit Follow-up System | {datetime.now().strftime('%d %b %Y')}")

with col_mode:
    if config.DRY_RUN:
        st.error("● DRY RUN MODE ACTIVE", icon="🚨")
    else:
        st.success("● LIVE SEND MODE", icon="🟢")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Agent Controls")
    run_btn = st.button("▶ Run Agent Now", type="primary", use_container_width=True)
    st.divider()
    st.markdown("### Quick Settings")
    st.toggle("Show LLM Reasoning", value=True)
    st.toggle("Auto-Refresh Audit", value=True)

# Load and classify records
if os.path.exists(config.CSV_PATH):
    records = load_invoices_from_csv(config.CSV_PATH)
    classified = [classify_record(r) for r in records]
else:
    st.error(f"CSV file not found at {config.CSV_PATH}")
    classified = []

# KPI metrics
if classified:
    total = len(classified)
    overdue = len([r for r in classified if r.days_overdue and r.days_overdue > 0])
    active = len([r for r in classified if r.stage and 1 <= r.stage <= 4])
    legal = len([r for r in classified if r.is_escalated])
    not_due = len([r for r in classified if r.stage and r.stage == 0])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f'<div class="kpi-card" style="border-top-color:#6c63ff"><div class="kpi-label">Total</div><div class="kpi-val" style="color:#6c63ff">{total}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card" style="border-top-color:#f59e0b"><div class="kpi-label">Overdue</div><div class="kpi-val" style="color:#f59e0b">{overdue}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card" style="border-top-color:#00d4aa"><div class="kpi-label">Active</div><div class="kpi-val" style="color:#00d4aa">{active}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card" style="border-top-color:#a855f7"><div class="kpi-label">Legal</div><div class="kpi-val" style="color:#a855f7">{legal}</div></div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="kpi-card" style="border-top-color:#64748b"><div class="kpi-label">Not Due</div><div class="kpi-val" style="color:#64748b">{not_due}</div></div>', unsafe_allow_html=True)

st.divider()

# Stage Tracker Rail
st.subheader("🎯 Escalation Stage Rail")
s1, s2, s3, s4, s5 = st.columns(5)
with s1:
    st.markdown('<div class="stage-item"><div class="stage-dot" style="background:#22c55e"></div><div style="color:#22c55e; font-weight:bold">STAGE 1</div><div style="font-size:0.7rem; color:#64748b">1-7 Days<br>Warm & Friendly</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown('<div class="stage-item"><div class="stage-dot" style="background:#f59e0b"></div><div style="color:#f59e0b; font-weight:bold">STAGE 2</div><div style="font-size:0.7rem; color:#64748b">8-14 Days<br>Polite & Firm</div></div>', unsafe_allow_html=True)
with s3:
    st.markdown('<div class="stage-item"><div class="stage-dot" style="background:#f97316"></div><div style="color:#f97316; font-weight:bold">STAGE 3</div><div style="font-size:0.7rem; color:#64748b">15-21 Days<br>Formal & Serious</div></div>', unsafe_allow_html=True)
with s4:
    st.markdown('<div class="stage-item"><div class="stage-dot" style="background:#ef4444"></div><div style="color:#ef4444; font-weight:bold">STAGE 4</div><div style="font-size:0.7rem; color:#64748b">22-30 Days<br>Stern & Urgent</div></div>', unsafe_allow_html=True)
with s5:
    st.markdown('<div class="stage-item"><div class="stage-dot" style="background:#a855f7"></div><div style="color:#a855f7; font-weight:bold">⚖ LEGAL</div><div style="font-size:0.7rem; color:#64748b">30+ Days<br>Human Review</div></div>', unsafe_allow_html=True)

st.divider()

# Invoice queue table
if classified:
    st.subheader("📋 Invoice Queue")
    df = pd.DataFrame([{
        "Invoice": r.invoice_no,
        "Client": r.client_name,
        "Amount": f"₹{r.amount:,.0f}",
        "Due Date": r.due_date,
        "Days Overdue": r.days_overdue or 0,
        "Stage": r.stage.name if r.stage else "N/A",
        "Status": "🚨 Legal" if r.is_escalated else "📧 Pending"
    } for r in classified])
    st.dataframe(df, use_container_width=True, hide_index=True)

# Audit log
st.subheader("📜 Audit Trail Feed")
if os.path.exists(config.AUDIT_JSON_PATH):
    try:
        with open(config.AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
        if audit_data:
            for entry in reversed(audit_data[-15:]):
                status_color = "#22c55e" if entry['send_status'] in ['sent', 'dry_run'] else "#ef4444"
                if entry['send_status'] == 'escalated': status_color = "#a855f7"
                
                with st.container():
                    col_meta, col_status = st.columns([5, 1])
                    with col_meta:
                        st.markdown(f"**{entry['invoice_no']}** | {entry['client_name']} | {entry['timestamp'][:19]}")
                    with col_status:
                        st.markdown(f"<span style='background:{status_color}22; color:{status_color}; padding:2px 8px; border-radius:10px; font-weight:bold'>{entry['send_status']}</span>", unsafe_allow_html=True)
                    
                    if entry.get('email_subject'):
                        with st.expander(f"👁 View Email: {entry['email_subject'][:50]}..."):
                            st.markdown(f"**Subject:** {entry['email_subject']}")
                            st.divider()
                            body_content = entry.get('email_body_preview') or 'No body content.'
                            st.markdown("**Body:**")
                            st.info(body_content)
                            st.caption(f"Tone: {entry.get('tone', 'N/A')}")
                    st.divider()
        else:
            st.info("Audit log is empty.")
    except Exception as e:
        st.error(f"Error loading audit log: {e}")
else:
    st.info("No audit entries yet. Run the agent to generate logs.")

# Run agent
if run_btn and classified:
    with st.spinner("🚀 Agent running in parallel..."):
        graph = build_agent_graph()
        
        # Filter records that need processing
        to_process = [r for r in classified if r.stage and r.stage != 0]
        
        if to_process:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def process_record(record):
                state = AgentState(
                    records=[record],
                    current_record=record, 
                    run_id=str(uuid.uuid4())
                )
                return graph.invoke(state)

            # Process in parallel (max 5 threads to avoid rate limits)
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(process_record, to_process))
                progress_bar.progress(100)
            
            st.success(f"✅ Agent run complete! Processed {len(to_process)} invoices.")
            st.balloons()
            st.rerun()
        else:
            st.info("No invoices require follow-up today.")
