import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LayoutDashboard, 
  Activity, 
  ShieldCheck, 
  Clock, 
  FileText, 
  ChevronRight, 
  Zap,
  Play,
  X,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Lock,
  Server,
  Mail,
  Search
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8000';

const App = () => {
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState({
    total: 0, overdue: 0, active: 0, legal: 0, pending_recovery: 0, injection_attempts: 0
  });
  const [logs, setLogs] = useState({ audit: [], workflow: [], ai: [], security: [] });
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [currentDraft, setCurrentDraft] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('Overview');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [invRes, statsRes, auditRes, wfRes, aiRes, secRes] = await Promise.all([
        axios.get(`${API_BASE}/invoices`),
        axios.get(`${API_BASE}/stats`),
        axios.get(`${API_BASE}/logs/audit`),
        axios.get(`${API_BASE}/logs/workflow`),
        axios.get(`${API_BASE}/logs/ai`),
        axios.get(`${API_BASE}/logs/security`)
      ]);
      setInvoices(invRes.data);
      setStats(statsRes.data);
      setLogs({
        audit: auditRes.data,
        workflow: wfRes.data,
        ai: aiRes.data,
        security: secRes.data
      });
    } catch (err) {
      console.error("Fetch failed", err);
    }
  };

  const handleGenerateDraft = async (invoiceNo) => {
    setIsGenerating(true);
    try {
      const res = await axios.post(`${API_BASE}/generate-draft/${invoiceNo}`);
      setCurrentDraft(res.data);
    } catch (err) {
      console.error("Draft generation failed", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunBatch = async () => {
    try {
      await axios.post(`${API_BASE}/run-batch`);
      fetchData();
    } catch (err) {
      console.error("Batch run failed", err);
    }
  };

  const Sidebar = () => (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <ShieldCheck size={24} />
          Finance AI
        </div>
      </div>
      <div className="sidebar-nav">
        {[
          { name: 'Overview', icon: LayoutDashboard },
          { name: 'Operations', icon: Activity },
          { name: 'Monitoring', icon: Clock },
          { name: 'Security', icon: ShieldCheck },
          { name: 'Audit Logs', icon: FileText },
        ].map((item) => (
          <button
            key={item.name}
            onClick={() => setActiveTab(item.name)}
            className={`nav-item ${activeTab === item.name ? 'active' : ''}`}
          >
            <item.icon className="nav-icon" />
            {item.name}
          </button>
        ))}
      </div>
      <div style={{ padding: '24px', borderTop: '1px solid var(--border)' }}>
        <div className="status-badge" style={{ backgroundColor: 'var(--bg)', border: '1px solid var(--border)' }}>
          <div className="status-dot active"></div>
          <span style={{ fontSize: '11px', opacity: 0.8 }}>Scheduler Active</span>
        </div>
      </div>
    </aside>
  );

  const TopBar = () => (
    <header className="top-bar">
      <div className="top-bar-left">
        <div className="status-badge">
          <div className="status-dot active"></div>
          Agent: Operational
        </div>
        <div className="status-badge" style={{ backgroundColor: 'oklch(95% 0.03 75)', color: 'var(--warning)' }}>
          <div className="status-dot warning"></div>
          Dry Run Mode
        </div>
        <span className="env-badge">Production</span>
      </div>
      <div className="top-bar-right">
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '12px', fontWeight: 600 }}>System Admin</div>
          <div style={{ fontSize: '10px', color: 'var(--muted)' }}>Last run: 2m ago</div>
        </div>
        <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--border)', overflow: 'hidden' }}>
          <img src="https://ui-avatars.com/api/?name=Admin&background=random" alt="User" />
        </div>
      </div>
    </header>
  );

  const DashboardBody = () => (
    <div className="dashboard-body">
      <div className="section-header">
        <h1 className="section-title">Finance Command Center</h1>
        <p style={{ color: 'var(--muted)', fontSize: '14px' }}>AI-powered automated credit follow-up & escalation.</p>
      </div>

      {/* KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Overdue Invoices</div>
          <div className="kpi-value">{stats.overdue}</div>
          <div className="kpi-trend trend-down">
            <TrendingDown size={12} />
            4.2% from peak
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Emails Sent Today</div>
          <div className="kpi-value">{logs.audit.length}</div>
          <div className="kpi-trend trend-up">
            <TrendingUp size={12} />
            12% vs avg
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Escalated Cases</div>
          <div className="kpi-value">{stats.legal}</div>
          <div className="kpi-trend trend-up" style={{ color: 'var(--escalation)' }}>Requires Review</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Pending Recovery</div>
          <div className="kpi-value">₹{(stats.pending_recovery / 1000).toFixed(1)}k</div>
          <div className="kpi-trend" style={{ color: 'var(--muted)' }}>Est. 85% success</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">AI Success Rate</div>
          <div className="kpi-value">94.2%</div>
          <div className="kpi-trend trend-up">
            <TrendingUp size={12} />
            0.8% improv.
          </div>
        </div>
      </div>

      {/* Pipeline Visualization */}
      <div className="pipeline-section">
        <div style={{ marginBottom: '20px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Invoice Escalation Pipeline</h2>
          <div style={{ fontSize: '12px', color: 'var(--muted)' }}>Real-time flow across 5 stages</div>
        </div>
        <div className="pipeline-viz">
          {[
            { name: 'Friendly', color: 'stage-1', count: invoices.filter(i => i.stage === 1).length },
            { name: 'Firm', color: 'stage-2', count: invoices.filter(i => i.stage === 2).length },
            { name: 'Serious', color: 'stage-3', count: invoices.filter(i => i.stage === 3).length },
            { name: 'Urgent', color: 'stage-4', count: invoices.filter(i => i.stage === 4).length },
            { name: 'Escalated', color: 'stage-esc', count: invoices.filter(i => i.is_escalated).length },
          ].map((stage) => (
            <div key={stage.name} className={`pipeline-stage ${stage.color}`}>
              <span className="stage-label">{stage.name}</span>
              <span className="stage-value">{stage.count}</span>
              <div className="stage-bar"></div>
            </div>
          ))}
        </div>
      </div>

      {/* Table Section */}
      <div className="table-section">
        <div style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Follow-Up Queue</h2>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-outline">Filter</button>
            <button className="btn btn-primary" onClick={handleRunBatch}>Run Batch</button>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Client Name</th>
              <th>Amount</th>
              <th>Overdue</th>
              <th>Stage</th>
              <th>Tone</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.invoice_no} onClick={() => {setSelectedInvoice(inv); setCurrentDraft(null);}} style={{ cursor: 'pointer' }}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>#{inv.invoice_no}</td>
                <td style={{ fontWeight: 500 }}>{inv.client_name}</td>
                <td>₹{inv.amount.toLocaleString()}</td>
                <td>{inv.days_overdue} Days</td>
                <td>Stage {inv.stage || 0}</td>
                <td><span className={`pill ${inv.stage > 3 ? 'pill-danger' : 'pill-info'}`}>{inv.stage > 3 ? 'Urgent' : 'Firm'}</span></td>
                <td><span className={`pill ${inv.is_escalated ? 'pill-warning' : 'pill-success'}`}>{inv.is_escalated ? 'ESCALATED' : 'QUEUED'}</span></td>
                <td><button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: '11px' }}>Inspect</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Panels Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px', marginBottom: '32px' }}>
        <div className="panel">
          <h3 className="panel-title"><Activity size={18} /> Observability & AI Monitoring</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>LLM Calls</div>
              <div style={{ fontWeight: 700, fontSize: '18px' }}>{logs.ai.length}</div>
            </div>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>Avg Latency</div>
              <div style={{ fontWeight: 700, fontSize: '18px' }}>{logs.ai[0]?.latency_ms || 0}ms</div>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3 className="panel-title"><ShieldCheck size={18} /> Security & Validation</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
              <span style={{ fontSize: '13px' }}>Prompt Injection Protection</span>
              <span className="pill pill-success">ACTIVE</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '13px' }}>Blocked Threats Today</span>
              <span style={{ color: 'var(--critical)', fontWeight: 800 }}>{stats.injection_attempts}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="panel" style={{ marginBottom: '64px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 className="panel-title" style={{ marginBottom: 0 }}><FileText size={18} /> Operational Audit Log</h3>
          <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Live Telemetry Stream</span>
        </div>
        <div className="audit-stream">
          {logs.audit.slice(-5).reverse().map((entry, idx) => (
            <div key={idx} className={`audit-entry ${entry.send_status === 'failed' ? 'warning' : 'success'}`}>
              <span style={{ fontWeight: 600 }}>{entry.timestamp.split('T')[1].split('.')[0]}</span> - Invoice <span style={{ fontFamily: 'var(--font-mono)' }}>#{entry.invoice_no}</span> follow-up generated. Status: {entry.send_status.toUpperCase()}.
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const Drawer = () => (
    <AnimatePresence>
      {selectedInvoice && (
        <>
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => {setSelectedInvoice(null); setCurrentDraft(null);}}
            className="fixed inset-0 bg-black/10 backdrop-blur-[2px] z-[200]"
          />
          <motion.div 
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            style={{ 
              position: 'fixed', right: 0, top: 0, width: '450px', height: '100vh', 
              backgroundColor: 'var(--surface)', borderLeft: '1px solid var(--border)', 
              zIndex: 210, boxShadow: '-10px 0 30px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column'
            }}
          >
            <div className="p-6 border-b border-border flex justify-between items-center bg-surface">
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Email Inspector</h3>
              <button className="btn btn-outline" style={{ padding: '6px' }} onClick={() => setSelectedInvoice(null)}><X size={18} /></button>
            </div>
            <div className="p-6 flex-grow overflow-y-auto space-y-6">
              <div>
                <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Generated Subject</div>
                <div style={{ fontWeight: 600, fontSize: '14px', padding: '12px', background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', color: 'var(--accent)' }}>
                  {currentDraft?.subject || `Draft Pending for #${selectedInvoice.invoice_no}`}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Tone Profile</div>
                  <span className="pill pill-warning">Firm & Professional</span>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Escalation Level</div>
                  <span className="pill pill-info">Stage {selectedInvoice.stage}</span>
                </div>
              </div>

              {!currentDraft ? (
                <button 
                  className="btn btn-primary w-full py-4 gap-2" 
                  onClick={() => handleGenerateDraft(selectedInvoice.invoice_no)}
                  disabled={isGenerating}
                >
                  {isGenerating ? <RefreshCw className="animate-spin" /> : <Zap size={18} />}
                  {isGenerating ? 'Analyzing Context...' : 'Generate Intelligence Draft'}
                </button>
              ) : (
                <div className="space-y-6">
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Body Preview</div>
                    <div className="email-preview">{currentDraft.body}</div>
                  </div>
                  <div className="panel" style={{ backgroundColor: 'oklch(99% 0.01 255)', borderFill: 'oklch(90% 0.02 255)', padding: '16px' }}>
                    <h4 style={{ fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}>
                      <Zap size={14} className="text-accent" /> AI Reasoning Trace
                    </h4>
                    <p style={{ fontSize: '11px', color: 'var(--muted)' }}>
                      Selected "{currentDraft.tone_confirmed}" because overdue threshold crossed. Validation score: 0.998.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn btn-primary flex-1">Approve & Send</button>
                    <button className="btn btn-outline flex-1" onClick={() => setCurrentDraft(null)}>Regenerate</button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <TopBar />
        <DashboardBody />
      </main>
      <Drawer />
    </div>
  );
};

export default App;
