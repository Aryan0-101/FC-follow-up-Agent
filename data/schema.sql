CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE NOT NULL,
    client_name TEXT NOT NULL,
    client_email TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    due_date DATE NOT NULL,
    follow_up_count INTEGER DEFAULT 0,
    contact_person TEXT,
    payment_link TEXT,
    is_escalated INTEGER DEFAULT 0,
    last_follow_up_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_email_masked TEXT NOT NULL,
    amount REAL NOT NULL,
    days_overdue INTEGER NOT NULL,
    stage INTEGER,
    tone TEXT,
    email_subject TEXT,
    email_body_preview TEXT,   -- First 200 chars only
    send_status TEXT,          -- sent | dry_run | failed | escalated
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
