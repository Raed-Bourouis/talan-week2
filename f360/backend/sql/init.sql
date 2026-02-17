-- ============================================================
-- F360 – Financial Command Center – Database Initialization
-- PostgreSQL + pgvector
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ──────────────────────────────────────────────
-- USERS & AUTH
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name       VARCHAR(255),
    role            VARCHAR(50) DEFAULT 'analyst',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- COMPANIES
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    siren       VARCHAR(20),
    sector      VARCHAR(100),
    country     VARCHAR(100) DEFAULT 'France',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- DEPARTMENTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID REFERENCES companies(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    code        VARCHAR(50),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- SUPPLIERS / CLIENTS (counterparties)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS counterparties (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(20) CHECK (type IN ('supplier', 'client')),
    tax_id          VARCHAR(50),
    contact_email   VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- CONTRACTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contracts (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID REFERENCES companies(id) ON DELETE CASCADE,
    counterparty_id     UUID REFERENCES counterparties(id),
    department_id       UUID REFERENCES departments(id),
    reference           VARCHAR(100) UNIQUE NOT NULL,
    title               VARCHAR(500),
    contract_type       VARCHAR(50),  -- 'service', 'supply', 'lease', 'consulting'
    start_date          DATE,
    end_date            DATE,
    total_amount        NUMERIC(18, 2),
    currency            VARCHAR(3) DEFAULT 'EUR',
    payment_terms       VARCHAR(255),
    penalty_clauses     TEXT,
    indexation_clause   TEXT,
    status              VARCHAR(30) DEFAULT 'active',  -- 'active', 'expired', 'terminated', 'draft'
    raw_text            TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- INVOICES
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID REFERENCES companies(id) ON DELETE CASCADE,
    contract_id         UUID REFERENCES contracts(id),
    counterparty_id     UUID REFERENCES counterparties(id),
    department_id       UUID REFERENCES departments(id),
    invoice_number      VARCHAR(100) NOT NULL,
    invoice_date        DATE NOT NULL,
    due_date            DATE,
    amount_ht           NUMERIC(18, 2) NOT NULL,
    amount_tax          NUMERIC(18, 2) DEFAULT 0,
    amount_ttc          NUMERIC(18, 2) NOT NULL,
    currency            VARCHAR(3) DEFAULT 'EUR',
    status              VARCHAR(30) DEFAULT 'pending',  -- 'pending', 'paid', 'overdue', 'disputed'
    payment_date        DATE,
    direction           VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    raw_text            TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- BUDGETS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budgets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    department_id   UUID REFERENCES departments(id),
    fiscal_year     INTEGER NOT NULL,
    category        VARCHAR(100),          -- 'OPEX', 'CAPEX', 'HR', 'IT', etc.
    planned_amount  NUMERIC(18, 2) NOT NULL,
    actual_amount   NUMERIC(18, 2) DEFAULT 0,
    currency        VARCHAR(3) DEFAULT 'EUR',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, department_id, fiscal_year, category)
);

-- ──────────────────────────────────────────────
-- ACCOUNTING ENTRIES
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accounting_entries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    invoice_id      UUID REFERENCES invoices(id),
    entry_date      DATE NOT NULL,
    journal_code    VARCHAR(20),
    account_number  VARCHAR(20) NOT NULL,
    label           VARCHAR(500),
    debit           NUMERIC(18, 2) DEFAULT 0,
    credit          NUMERIC(18, 2) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- DOCUMENTS (uploaded files metadata)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    filename        VARCHAR(500) NOT NULL,
    file_type       VARCHAR(20),          -- 'pdf', 'xlsx', 'docx', 'email'
    file_path       TEXT,
    file_size_bytes BIGINT,
    entity_type     VARCHAR(50),          -- 'contract', 'invoice', 'budget', 'email'
    entity_id       UUID,                 -- FK to related entity
    processed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- DOCUMENT CHUNKS (for RAG / vector search)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    embedding       vector(1536),          -- OpenAI text-embedding-3-small dimension
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (IVFFlat for large datasets)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm
    ON document_chunks
    USING gin (content gin_trgm_ops);

-- ──────────────────────────────────────────────
-- CASHFLOW ENTRIES (for projection)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cashflow_entries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    entry_date      DATE NOT NULL,
    amount          NUMERIC(18, 2) NOT NULL,
    direction       VARCHAR(10) CHECK (direction IN ('in', 'out')),
    category        VARCHAR(100),
    source          VARCHAR(100),         -- 'invoice', 'contract', 'manual'
    source_id       UUID,
    is_projected    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- RECOMMENDATIONS LOG
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    category        VARCHAR(50),          -- 'budget', 'contract', 'cashflow', 'risk'
    severity        VARCHAR(20),          -- 'info', 'warning', 'critical'
    title           VARCHAR(500),
    description     TEXT,
    suggested_action TEXT,
    entity_type     VARCHAR(50),
    entity_id       UUID,
    is_resolved     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- SIMULATION RESULTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulation_results (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id),
    simulation_type VARCHAR(50),          -- 'budget_variation', 'cashflow_projection', 'monte_carlo', 'renegotiation'
    parameters      JSONB NOT NULL,
    results         JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- USEFUL INDEXES
-- ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_invoices_company ON invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_contracts_company ON contracts(company_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_budgets_company_year ON budgets(company_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_cashflow_date ON cashflow_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_recommendations_company ON recommendations(company_id);
CREATE INDEX IF NOT EXISTS idx_documents_entity ON documents(entity_type, entity_id);
