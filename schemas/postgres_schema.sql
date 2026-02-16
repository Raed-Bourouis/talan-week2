-- PostgreSQL Schema for Financial Intelligence Hub
-- This schema stores structured financial metadata and audit trails

-- Enable pgvector extension for hybrid search
CREATE EXTENSION IF NOT EXISTS vector;

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    fiscal_year_start DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(50) PRIMARY KEY,
    company_id VARCHAR(50) REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    head VARCHAR(255),
    cost_center VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Budgets table
CREATE TABLE IF NOT EXISTS budgets (
    id VARCHAR(50) PRIMARY KEY,
    department_id VARCHAR(50) REFERENCES departments(id),
    year INTEGER NOT NULL,
    quarter VARCHAR(10),
    allocated_amount DECIMAL(15, 2) NOT NULL,
    spent_amount DECIMAL(15, 2) DEFAULT 0,
    variance DECIMAL(15, 2),
    variance_percent DECIMAL(5, 4),
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    payment_terms VARCHAR(50),
    risk_score DECIMAL(3, 2),
    reliability_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contracts table
CREATE TABLE IF NOT EXISTS contracts (
    id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) REFERENCES suppliers(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    value DECIMAL(15, 2) NOT NULL,
    status VARCHAR(50),
    auto_renew BOOLEAN DEFAULT FALSE,
    payment_terms VARCHAR(50),
    clauses JSONB,
    document_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id VARCHAR(50) PRIMARY KEY,
    contract_id VARCHAR(50) REFERENCES contracts(id),
    supplier_id VARCHAR(50) REFERENCES suppliers(id),
    department_id VARCHAR(50) REFERENCES departments(id),
    invoice_number VARCHAR(100) NOT NULL UNIQUE,
    amount DECIMAL(15, 2) NOT NULL,
    tax_amount DECIMAL(15, 2),
    total_amount DECIMAL(15, 2),
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    status VARCHAR(50),
    days_late INTEGER,
    document_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(50) PRIMARY KEY,
    invoice_id VARCHAR(50) REFERENCES invoices(id),
    amount DECIMAL(15, 2) NOT NULL,
    date DATE NOT NULL,
    method VARCHAR(50),
    reference VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    payment_reliability DECIMAL(3, 2),
    average_payment_delay INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table for tracking uploaded files
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    category VARCHAR(100),
    file_path VARCHAR(500),
    file_size INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    embedding vector(1536)  -- For hybrid search with pgvector
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255)
);

-- Simulations table for tracking scenario analyses
CREATE TABLE IF NOT EXISTS simulations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    parameters JSONB,
    results JSONB,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    changes JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_budgets_department ON budgets(department_id);
CREATE INDEX idx_budgets_year ON budgets(year);
CREATE INDEX idx_contracts_supplier ON contracts(supplier_id);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_end_date ON contracts(end_date);
CREATE INDEX idx_invoices_contract ON invoices(contract_id);
CREATE INDEX idx_invoices_supplier ON invoices(supplier_id);
CREATE INDEX idx_invoices_department ON invoices(department_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_type ON alerts(type);

-- Insert sample data
INSERT INTO companies (id, name, industry, fiscal_year_start) VALUES
('COMPANY001', 'Acme Financial Corp', 'Financial Services', '2024-01-01');

INSERT INTO departments (id, company_id, name, head, cost_center) VALUES
('DEPT001', 'COMPANY001', 'Marketing', 'John Smith', 'CC-MKT-001'),
('DEPT002', 'COMPANY001', 'R&D', 'Jane Doe', 'CC-RD-001'),
('DEPT003', 'COMPANY001', 'Operations', 'Bob Johnson', 'CC-OPS-001');

INSERT INTO budgets (id, department_id, year, quarter, allocated_amount, spent_amount, variance, variance_percent, status) VALUES
('BUDGET-2024-MKT', 'DEPT001', 2024, 'Q1', 500000.00, 575000.00, -75000.00, -0.15, 'over_budget'),
('BUDGET-2024-RD', 'DEPT002', 2024, 'Q1', 800000.00, 720000.00, 80000.00, 0.10, 'under_budget');

INSERT INTO suppliers (id, name, category, payment_terms, risk_score, reliability_score) VALUES
('SUPP001', 'TechVendor Inc', 'Technology', 'Net 30', 0.2, 0.85),
('SUPP002', 'Office Solutions Ltd', 'Office Supplies', 'Net 45', 0.1, 0.95);

INSERT INTO contracts (id, supplier_id, name, start_date, end_date, value, status, auto_renew, payment_terms, clauses) VALUES
('CONTRACT001', 'SUPP001', 'Annual Software License', '2024-01-01', '2024-12-31', 120000.00, 'active', true, 'Net 30', 
 '["Auto-renewal", "Price indexation +3%", "SLA 99.9%"]'::jsonb),
('CONTRACT002', 'SUPP002', 'Office Supplies Framework', '2024-01-01', '2024-06-30', 50000.00, 'expiring_soon', false, 'Net 45',
 '["Volume discount", "Quarterly review"]'::jsonb);

INSERT INTO invoices (id, contract_id, supplier_id, department_id, invoice_number, amount, tax_amount, total_amount, issue_date, due_date, payment_date, status, days_late) VALUES
('INV001', 'CONTRACT001', 'SUPP001', 'DEPT002', 'INV-2024-001', 10000.00, 2000.00, 12000.00, '2024-01-15', '2024-02-14', '2024-02-20', 'paid_late', 6),
('INV002', 'CONTRACT002', 'SUPP002', 'DEPT003', 'INV-2024-002', 5000.00, 1000.00, 6000.00, '2024-01-20', '2024-03-06', NULL, 'pending', 0);

INSERT INTO payments (id, invoice_id, amount, date, method, reference) VALUES
('PAY001', 'INV001', 12000.00, '2024-02-20', 'Wire Transfer', 'WT-2024-001');

INSERT INTO clients (id, name, category, payment_reliability, average_payment_delay) VALUES
('CLIENT001', 'Enterprise Customer', 'Enterprise', 0.92, 5);

INSERT INTO alerts (type, severity, title, description, entity_type, entity_id, status) VALUES
('budget', 'high', 'Marketing Budget Exceeded', 'Marketing department is 15% over budget', 'department', 'DEPT001', 'active'),
('contract', 'medium', 'Contract Expiring Soon', 'Office Supplies Framework expires in 90 days', 'contract', 'CONTRACT002', 'active'),
('payment', 'low', 'Late Payment Detected', 'Invoice INV-2024-001 paid 6 days late', 'invoice', 'INV001', 'active');
