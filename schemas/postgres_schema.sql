-- ================================================================
-- FINCENTER PostgreSQL Schema
-- Structured Financial Metadata with pgvector support
-- ================================================================

-- Enable pgvector extension for hybrid search
CREATE EXTENSION IF NOT EXISTS vector;

-- ================================================================
-- CORE ENTITIES
-- ================================================================

-- Documents table for tracking all financial documents
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- budget, contract, invoice, accounting
    file_path VARCHAR(1000),
    file_size BIGINT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processed, error
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document chunks for RAG (with vector embeddings)
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384), -- all-MiniLM-L6-v2 produces 384-dimensional embeddings
    token_count INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ================================================================
-- FINANCIAL ENTITIES
-- ================================================================

-- Departments
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    department_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    budget_allocated DECIMAL(15, 2),
    budget_spent DECIMAL(15, 2) DEFAULT 0,
    manager VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(300) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    budget DECIMAL(15, 2),
    spent DECIMAL(15, 2) DEFAULT 0,
    status VARCHAR(50), -- planning, active, completed, on-hold
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    supplier_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(300) NOT NULL,
    contact_email VARCHAR(200),
    contact_phone VARCHAR(50),
    payment_terms VARCHAR(50), -- NET30, NET45, NET60
    reliability_score DECIMAL(3, 2), -- 0.00 to 1.00
    avg_delay_days INTEGER DEFAULT 0,
    total_contracts INTEGER DEFAULT 0,
    total_paid DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id SERIAL PRIMARY KEY,
    contract_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id),
    contract_value DECIMAL(15, 2),
    start_date DATE,
    expiration_date DATE,
    status VARCHAR(50), -- active, expired, terminated, pending
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_terms VARCHAR(100),
    penalty_clause TEXT,
    clauses JSONB, -- Extracted clauses from LLM
    document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_id VARCHAR(50) UNIQUE NOT NULL,
    invoice_number VARCHAR(100) NOT NULL,
    contract_id INTEGER REFERENCES contracts(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    amount DECIMAL(15, 2) NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    status VARCHAR(50), -- pending, paid, overdue, cancelled
    document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(50) UNIQUE NOT NULL,
    invoice_id INTEGER REFERENCES invoices(id),
    amount DECIMAL(15, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50), -- bank_transfer, check, credit_card
    status VARCHAR(50), -- pending, completed, failed
    reference_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Budget allocations
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    budget_id VARCHAR(50) UNIQUE NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    period VARCHAR(50), -- Q1 2024, Q2 2024, etc.
    fiscal_year INTEGER,
    allocated DECIMAL(15, 2) NOT NULL,
    spent DECIMAL(15, 2) DEFAULT 0,
    variance DECIMAL(15, 2),
    variance_pct DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    expense_id VARCHAR(50) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    department_id INTEGER REFERENCES departments(id),
    category VARCHAR(100),
    amount DECIMAL(15, 2) NOT NULL,
    expense_date DATE NOT NULL,
    description TEXT,
    invoice_id INTEGER REFERENCES invoices(id),
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- ANALYTICS & EPISODIC MEMORY
-- ================================================================

-- Patterns detected by episodic memory system
CREATE TABLE IF NOT EXISTS patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(50) UNIQUE NOT NULL,
    pattern_type VARCHAR(100), -- late_payment, budget_overrun, seasonal, etc.
    description TEXT,
    confidence DECIMAL(3, 2), -- 0.00 to 1.00
    occurrences INTEGER DEFAULT 1,
    first_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    related_entities JSONB, -- References to suppliers, departments, etc.
    recommendation TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, resolved, monitoring
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts and recommendations
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE NOT NULL,
    alert_type VARCHAR(100), -- budget, contract, payment, risk, optimization
    severity VARCHAR(20), -- low, medium, high, critical
    title VARCHAR(500) NOT NULL,
    description TEXT,
    entity_type VARCHAR(50), -- department, contract, supplier, invoice
    entity_id VARCHAR(50),
    recommendation TEXT,
    status VARCHAR(50) DEFAULT 'open', -- open, acknowledged, resolved, dismissed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cash flow predictions
CREATE TABLE IF NOT EXISTS cash_flow_predictions (
    id SERIAL PRIMARY KEY,
    prediction_date DATE NOT NULL,
    predicted_inflow DECIMAL(15, 2),
    predicted_outflow DECIMAL(15, 2),
    predicted_balance DECIMAL(15, 2),
    confidence_lower DECIMAL(15, 2), -- Lower bound of confidence interval
    confidence_upper DECIMAL(15, 2), -- Upper bound of confidence interval
    actual_inflow DECIMAL(15, 2),
    actual_outflow DECIMAL(15, 2),
    actual_balance DECIMAL(15, 2),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query history for learning
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_type VARCHAR(100),
    response TEXT,
    context_used JSONB,
    user_feedback INTEGER, -- 1-5 rating
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_contracts_expiration ON contracts(expiration_date);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- ================================================================
-- SAMPLE DATA
-- ================================================================

-- Insert sample departments
INSERT INTO departments (department_id, name, budget_allocated, budget_spent, manager)
VALUES 
    ('DEPT-001', 'Marketing', 500000, 425000, 'Jane Smith'),
    ('DEPT-002', 'R&D', 800000, 680000, 'John Doe'),
    ('DEPT-003', 'Operations', 600000, 520000, 'Bob Johnson'),
    ('DEPT-004', 'Sales', 400000, 350000, 'Alice Williams')
ON CONFLICT (department_id) DO NOTHING;

-- Insert sample suppliers
INSERT INTO suppliers (supplier_id, name, contact_email, payment_terms, reliability_score, avg_delay_days)
VALUES 
    ('SUP-001', 'TechVendor Inc', 'contact@techvendor.com', 'NET30', 0.85, 5),
    ('SUP-002', 'Marketing Agency Pro', 'sales@marketingpro.com', 'NET45', 0.92, 2),
    ('SUP-003', 'Cloud Services Ltd', 'billing@cloudservices.com', 'NET30', 0.78, 12)
ON CONFLICT (supplier_id) DO NOTHING;

-- Insert sample alerts
INSERT INTO alerts (alert_id, alert_type, severity, title, description, entity_type, entity_id, recommendation)
VALUES 
    ('ALERT-001', 'budget', 'high', 'Marketing Budget Overrun', 'Marketing department has exceeded budget by 15%', 'department', 'DEPT-001', 'Review marketing spend and implement stricter controls'),
    ('ALERT-002', 'contract', 'medium', 'Contract Expiring Soon', 'Software License Agreement expires in 45 days', 'contract', 'CONT-001', 'Start renewal negotiations with supplier'),
    ('ALERT-003', 'payment', 'critical', 'Overdue Invoice', 'Invoice INV-2024-002 is 30 days overdue', 'invoice', 'INV-002', 'Contact supplier immediately regarding payment')
ON CONFLICT (alert_id) DO NOTHING;

-- ================================================================
-- FUNCTIONS & TRIGGERS
-- ================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%s_updated_at ON %s', t, t);
        EXECUTE format('CREATE TRIGGER update_%s_updated_at 
                       BEFORE UPDATE ON %s 
                       FOR EACH ROW 
                       EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- ================================================================
-- VIEWS FOR COMMON QUERIES
-- ================================================================

-- Budget variance view
CREATE OR REPLACE VIEW budget_variance_summary AS
SELECT 
    d.department_id,
    d.name as department_name,
    d.budget_allocated,
    d.budget_spent,
    (d.budget_allocated - d.budget_spent) as remaining,
    CASE 
        WHEN d.budget_allocated > 0 
        THEN ((d.budget_spent - d.budget_allocated) / d.budget_allocated * 100)
        ELSE 0 
    END as variance_pct
FROM departments d;

-- Overdue invoices view
CREATE OR REPLACE VIEW overdue_invoices AS
SELECT 
    i.invoice_id,
    i.invoice_number,
    s.name as supplier_name,
    i.amount,
    i.due_date,
    CURRENT_DATE - i.due_date as days_overdue
FROM invoices i
JOIN suppliers s ON i.supplier_id = s.id
WHERE i.status = 'overdue' AND i.payment_date IS NULL
ORDER BY days_overdue DESC;

-- Contract expiration view
CREATE OR REPLACE VIEW expiring_contracts AS
SELECT 
    c.contract_id,
    c.title,
    s.name as supplier_name,
    c.contract_value,
    c.expiration_date,
    c.expiration_date - CURRENT_DATE as days_until_expiration,
    c.auto_renewal
FROM contracts c
JOIN suppliers s ON c.supplier_id = s.id
WHERE c.status = 'active' 
AND c.expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
ORDER BY c.expiration_date;

-- Active alerts view
CREATE OR REPLACE VIEW active_alerts AS
SELECT 
    alert_id,
    alert_type,
    severity,
    title,
    description,
    recommendation,
    created_at
FROM alerts
WHERE status = 'open'
ORDER BY 
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    created_at DESC;
