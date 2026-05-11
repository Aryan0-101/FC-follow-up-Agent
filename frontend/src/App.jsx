import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ShieldCheck, 
  ChevronRight, 
  Zap,
  Play,
  X,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  FileText,
  Mail,
  Clock,
  CheckCircle2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8000';

const App = () => {
    const [invoices, setInvoices] = useState([]);
    const [stats, setStats] = useState({ total: 0, overdue: 0, active: 0, legal: 0, pending_recovery: 0, injection_attempts: 0 });
    const [logs, setLogs] = useState({ audit: [], workflow: [], ai: [], security: [] });
    const [selectedInvoice, setSelectedInvoice] = useState(null);
    const [currentDraft, setCurrentDraft] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [isSent, setIsSent] = useState(false);
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [isRunningBatch, setIsRunningBatch] = useState(false);
    const [schedStatus, setSchedStatus] = useState({ active: false, next_run: null, timeLeft: '' });

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const timer = setInterval(() => {
            if (schedStatus.next_run) {
                const now = new Date();
                const next = new Date(schedStatus.next_run);
                const diff = next - now;
                if (diff > 0) {
                    const hours = Math.floor(diff / (1000 * 60 * 60));
                    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    const secs = Math.floor((diff % (1000 * 60)) / 1000);
                    setSchedStatus(prev => ({ ...prev, timeLeft: `${hours}h ${mins}m ${secs}s` }));
                } else {
                    setSchedStatus(prev => ({ ...prev, timeLeft: 'Running...' }));
                }
            }
        }, 1000);
        return () => clearInterval(timer);
    }, [schedStatus.next_run]);

    const fetchData = async () => {
        try {
            const [invRes, statsRes, auditRes, aiRes, schedRes] = await Promise.all([
                axios.get(`${API_BASE}/invoices`),
                axios.get(`${API_BASE}/stats`),
                axios.get(`${API_BASE}/logs/audit`),
                axios.get(`${API_BASE}/logs/ai`),
                axios.get(`${API_BASE}/scheduler/status`)
            ]);
            setInvoices(invRes.data);
            setStats(statsRes.data);
            setLogs(prev => ({ ...prev, audit: auditRes.data, ai: aiRes.data }));
            setSchedStatus(prev => ({ ...prev, active: schedRes.data.active, next_run: schedRes.data.next_run }));
        } catch (err) {
            console.error("Fetch failed", err);
        }
    };

    const handleGenerateDraft = async (invoiceNo) => {
        setIsGenerating(true);
        setIsSent(false);
        try {
            const res = await axios.post(`${API_BASE}/generate-draft/${invoiceNo}`);
            setCurrentDraft(res.data);
        } catch (err) {
            console.error("Draft generation failed", err);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSendDraft = async () => {
        setIsSending(true);
        try {
            await axios.post(`${API_BASE}/send-draft/${selectedInvoice.invoice_no}`, currentDraft);
            setIsSent(true);
            fetchData();
        } catch (err) {
            console.error("Send failed", err);
        } finally {
            setIsSending(false);
        }
    };

    const handleRunBatch = async () => {
        setIsRunningBatch(true);
        try {
            await axios.post(`${API_BASE}/run-batch`);
            // Show loading for a bit to give feedback
            setTimeout(() => {
                setIsRunningBatch(false);
                fetchData();
            }, 3000);
        } catch (err) {
            console.error("Batch run failed", err);
            setIsRunningBatch(false);
        }
    };

    const openDrawer = (invoice) => {
        setSelectedInvoice(invoice);
        setCurrentDraft(null);
        setIsSent(false);
        setIsDrawerOpen(true);
    };

    return (
        <div className="app-container" style={{ display: 'block' }}>
            {/* Header / Top Bar */}
            <header className="top-bar">
                <div className="top-bar-left">
                    <div className="logo" style={{ marginRight: '32px' }}>
                        <ShieldCheck size={24} />
                        Finance AI
                    </div>
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
                        <div style={{ fontSize: '10px', color: 'var(--muted)' }}>Monitoring Active</div>
                    </div>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--border)', overflow: 'hidden' }}>
                        <img src="https://ui-avatars.com/api/?name=Admin&background=random" alt="User" />
                    </div>
                </div>
            </header>

            <main className="main-content" style={{ marginLeft: 0 }}>
                <div className="dashboard-body">
                    <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                        <div>
                            <h1 className="section-title">Finance Command Center</h1>
                            <p style={{ color: 'var(--muted)', fontSize: '14px' }}>AI-powered automated credit follow-up & escalation.</p> 
                        </div>
                        {/* Scheduler Status Section */}
                        <div className="panel" style={{ padding: '12px 24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
                           <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                               <Clock size={16} className="text-accent" />
                               <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Next Automation Run</span>
                           </div>
                           <div style={{ fontSize: '18px', fontWeight: 800, fontMono: 'var(--font-mono)', color: 'var(--accent)' }}>
                               {schedStatus.timeLeft || 'Calculating...'}
                           </div>
                           <div className="pill pill-success" style={{ padding: '4px 10px' }}>Active</div>
                        </div>
                    </div>

                    {/* KPI Cards */}
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
                            <div className="kpi-label">Follow-ups Sent</div>
                            <div className="kpi-value">{logs.audit.length}</div>
                            <div className="kpi-trend trend-up">
                                <TrendingUp size={12} />
                                12% vs avg
                            </div>
                        </div>
                        <div className="kpi-card">
                            <div className="kpi-label">Escalated Cases</div>
                            <div className="kpi-value" style={{ color: 'var(--escalation)' }}>{stats.legal}</div>
                            <div className="kpi-trend trend-up" style={{ color: 'var(--escalation)' }}>Legal Action</div>
                        </div>
                        <div className="kpi-card">
                            <div className="kpi-label">Pending Recovery</div>
                            <div className="kpi-value">₹{(stats.pending_recovery/1000).toFixed(1)}k</div>
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

                    {/* Pipeline */}
                    <div className="pipeline-section">
                        <div style={{ marginBottom: '20px' }}>
                            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Invoice Escalation Pipeline</h2>
                            <div style={{ fontSize: '12px', color: 'var(--muted)' }}>Real-time flow across 5 stages</div>
                        </div>
                        <div className="pipeline-viz">
                            <div className="pipeline-stage stage-1">
                                <span className="stage-label">Friendly</span>
                                <span className="stage-value">{invoices.filter(i => i.stage === 1).length}</span>
                                <div className="stage-bar"></div>
                            </div>
                            <div className="pipeline-stage stage-2">
                                <span className="stage-label">Firm</span>
                                <span className="stage-value">{invoices.filter(i => i.stage === 2).length}</span>
                                <div className="stage-bar"></div>
                            </div>
                            <div className="pipeline-stage stage-3">
                                <span className="stage-label">Serious</span>
                                <span className="stage-value">{invoices.filter(i => i.stage === 3).length}</span>
                                <div className="stage-bar"></div>
                            </div>
                            <div className="pipeline-stage stage-4">
                                <span className="stage-label">Urgent</span>
                                <span className="stage-value">{invoices.filter(i => i.stage === 4).length}</span>
                                <div className="stage-bar"></div>
                            </div>
                            <div className="pipeline-stage stage-esc">
                                <span className="stage-label">Escalated</span>
                                <span className="stage-value">{invoices.filter(i => i.is_escalated).length}</span>
                                <div className="stage-bar"></div>
                            </div>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="table-section">
                        <div style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Follow-Up Queue</h2>
                            <div style={{ display: 'flex', gap: '12px' }}>
                                <button className="btn btn-outline">Filter</button>
                                <button 
                                    className="btn btn-primary" 
                                    onClick={handleRunBatch}
                                    disabled={isRunningBatch}
                                    style={{ gap: '8px', minWidth: '140px' }}
                                >
                                    {isRunningBatch ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
                                    {isRunningBatch ? 'Processing...' : 'Run Batch'}
                                </button>
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
                                    <tr key={inv.invoice_no} onClick={() => openDrawer(inv)} style={{ cursor: 'pointer' }}>
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

                    <div className="panels-grid">
                        <div className="panel">
                            <h3 className="panel-title"><Activity size={18} /> Observability & Monitoring</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <div style={{ padding: '12px', backgroundColor: 'var(--bg)', borderRadius: 'var(--radius-md)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>LLM Latency</div>
                                    <div style={{ fontWeight: 700, fontSize: '18px' }}>{logs.ai[0]?.latency_ms || 0}ms</div>
                                </div>
                                <div style={{ padding: '12px', backgroundColor: 'var(--bg)', borderRadius: 'var(--radius-md)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>AI Confidence</div>
                                    <div style={{ fontWeight: 700, fontSize: '18px', color: 'var(--success)' }}>High (98%)</div>
                                </div>
                            </div>
                        </div>
                        <div className="panel">
                            <h3 className="panel-title"><ShieldCheck size={18} /> Security Status</h3>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px' }}>Blocked Injection Attempts</span>
                                <span style={{ color: 'var(--critical)', fontWeight: 800, fontSize: '20px' }}>{stats.injection_attempts}</span>
                            </div>
                        </div>
                    </div>

                    {/* Audit Logs */}
                    <div className="panel" style={{ marginBottom: '64px' }}>
                        <h3 className="panel-title" style={{ marginBottom: '20px' }}>
                            <FileText size={18} /> Operational Audit Log
                        </h3>
                        <div className="audit-stream">
                            {logs.audit.slice(-5).reverse().map((entry, idx) => (
                                <div key={idx} className="audit-entry success">
                                    <span style={{ fontWeight: 600 }}>{entry.timestamp.split('T')[1].split('.')[0]}</span> - Invoice <span style={{ fontFamily: 'var(--font-mono)' }}>#{entry.invoice_no}</span> follow-up generated. Status: {entry.send_status.toUpperCase()}.
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </main>

            {/* Right Drawer */}
            <div className={`drawer ${isDrawerOpen ? 'open' : ''}`}>
                <div className="drawer-header">
                    <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Email Inspector</h3>
                    <button className="btn btn-outline" style={{ padding: '6px' }} onClick={() => setIsDrawerOpen(false)}><X size={18} /></button>
                </div>
                <div className="drawer-body">
                    {selectedInvoice && (
                        <>
                            <div style={{ marginBottom: '24px' }}>
                                <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Target Recipient</div>
                                <div style={{ fontWeight: 600, fontSize: '14px', padding: '12px', background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                                    {selectedInvoice.client_name} ({selectedInvoice.client_email})
                                </div>
                            </div>

                            {/* Restrict draft for escalated/stage 0 */}
                            {(selectedInvoice.is_escalated || selectedInvoice.stage === 0) ? (
                                <div style={{ padding: '20px', background: 'oklch(97% 0.01 250)', borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px dashed var(--border)' }}>
                                    <p style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: 500 }}>
                                        {selectedInvoice.is_escalated ? 
                                            '⚠️ Draft generation disabled. This invoice has been escalated for legal review.' : 
                                            'ℹ️ Draft generation disabled. This invoice is not yet overdue.'
                                        }
                                    </p>
                                </div>
                            ) : !currentDraft ? (
                                <button className="btn btn-primary" style={{ width: '100%', padding: '12px', gap: '8px' }} onClick={() => handleGenerateDraft(selectedInvoice.invoice_no)} disabled={isGenerating}>
                                    {isGenerating ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
                                    {isGenerating ? 'AI Analysis in Progress...' : 'Generate Intelligence Draft'}
                                </button>
                            ) : (
                                <>
                                    <div style={{ marginBottom: '24px' }}>
                                        <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Generated Subject</div>
                                        <div style={{ fontWeight: 600, fontSize: '14px', padding: '12px', background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', color: 'var(--accent)' }}>
                                            {currentDraft.subject}
                                        </div>
                                    </div>
                                    <div style={{ marginBottom: '24px' }}>
                                        <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>Body Preview</div>
                                        <div className="email-preview">{currentDraft.body}</div>
                                    </div>
                                    
                                    {isSent ? (
                                        <div style={{ padding: '16px', background: 'oklch(96% 0.03 150)', color: 'var(--success)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                            <CheckCircle2 size={20} />
                                            <div style={{ fontSize: '13px', fontWeight: 600 }}>Email successfully sent to {selectedInvoice.client_email}</div>
                                        </div>
                                    ) : (
                                        <div style={{ marginTop: '32px', display: 'flex', gap: '12px' }}>
                                            <button 
                                                className="btn btn-primary" 
                                                style={{ flex: 1, gap: '8px' }} 
                                                onClick={handleSendDraft}
                                                disabled={isSending}
                                            >
                                                {isSending ? <RefreshCw size={16} className="animate-spin" /> : <Mail size={16} />}
                                                {isSending ? 'Sending...' : 'Approve & Send'}
                                            </button>
                                            <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => setCurrentDraft(null)}>Regenerate</button>
                                        </div>
                                    )}
                                </>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default App;
