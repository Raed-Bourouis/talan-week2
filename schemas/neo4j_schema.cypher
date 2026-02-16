// ================================================================
// FINCENTER Neo4j Graph Schema
// Financial Entity Relationships and Patterns
// ================================================================

// Create constraints for unique identifiers
CREATE CONSTRAINT IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (pay:Payment) REQUIRE pay.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (b:Budget) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (e:Expense) REQUIRE e.id IS UNIQUE;

// Create indexes for frequently queried properties
CREATE INDEX IF NOT EXISTS FOR (c:Contract) ON (c.status);
CREATE INDEX IF NOT EXISTS FOR (c:Contract) ON (c.expiration_date);
CREATE INDEX IF NOT EXISTS FOR (i:Invoice) ON (i.status);
CREATE INDEX IF NOT EXISTS FOR (i:Invoice) ON (i.due_date);
CREATE INDEX IF NOT EXISTS FOR (pay:Payment) ON (pay.date);
CREATE INDEX IF NOT EXISTS FOR (e:Expense) ON (e.date);

// ================================================================
// SAMPLE DATA - Financial Entities
// ================================================================

// Departments
MERGE (d1:Department {id: 'DEPT-001', name: 'Marketing', budget_allocated: 500000})
MERGE (d2:Department {id: 'DEPT-002', name: 'R&D', budget_allocated: 800000})
MERGE (d3:Department {id: 'DEPT-003', name: 'Operations', budget_allocated: 600000})
MERGE (d4:Department {id: 'DEPT-004', name: 'Sales', budget_allocated: 400000});

// Projects
MERGE (p1:Project {id: 'PROJ-001', name: 'Digital Campaign Q1', budget: 150000, status: 'active'})
MERGE (p2:Project {id: 'PROJ-002', name: 'Product Development', budget: 300000, status: 'active'})
MERGE (p3:Project {id: 'PROJ-003', name: 'Infrastructure Upgrade', budget: 200000, status: 'planning'});

// Suppliers
MERGE (s1:Supplier {
    id: 'SUP-001', 
    name: 'TechVendor Inc', 
    payment_terms: 'NET30',
    reliability_score: 0.85,
    avg_delay_days: 5
})
MERGE (s2:Supplier {
    id: 'SUP-002', 
    name: 'Marketing Agency Pro', 
    payment_terms: 'NET45',
    reliability_score: 0.92,
    avg_delay_days: 2
})
MERGE (s3:Supplier {
    id: 'SUP-003', 
    name: 'Cloud Services Ltd', 
    payment_terms: 'NET30',
    reliability_score: 0.78,
    avg_delay_days: 12
});

// Contracts
MERGE (c1:Contract {
    id: 'CONT-001',
    title: 'Software License Agreement',
    start_date: date('2024-01-01'),
    expiration_date: date('2024-12-31'),
    value: 120000,
    status: 'active',
    auto_renewal: true,
    penalty_clause: 'Late payment: 2% per month'
})
MERGE (c2:Contract {
    id: 'CONT-002',
    title: 'Marketing Services 2024',
    start_date: date('2024-03-01'),
    expiration_date: date('2024-09-30'),
    value: 80000,
    status: 'active',
    auto_renewal: false,
    penalty_clause: 'Termination: 30 days notice'
})
MERGE (c3:Contract {
    id: 'CONT-003',
    title: 'Cloud Infrastructure',
    start_date: date('2023-06-01'),
    expiration_date: date('2026-05-31'),
    value: 360000,
    status: 'active',
    auto_renewal: true,
    penalty_clause: 'SLA breach: 10% credit'
});

// Invoices
MERGE (i1:Invoice {
    id: 'INV-001',
    number: 'INV-2024-001',
    amount: 10000,
    issue_date: date('2024-01-15'),
    due_date: date('2024-02-14'),
    status: 'paid',
    payment_date: date('2024-02-12')
})
MERGE (i2:Invoice {
    id: 'INV-002',
    number: 'INV-2024-002',
    amount: 15000,
    issue_date: date('2024-02-01'),
    due_date: date('2024-03-03'),
    status: 'overdue',
    payment_date: null
})
MERGE (i3:Invoice {
    id: 'INV-003',
    number: 'INV-2024-003',
    amount: 30000,
    issue_date: date('2024-02-15'),
    due_date: date('2024-03-17'),
    status: 'pending',
    payment_date: null
});

// Payments
MERGE (pay1:Payment {
    id: 'PAY-001',
    amount: 10000,
    date: date('2024-02-12'),
    method: 'bank_transfer',
    status: 'completed'
})
MERGE (pay2:Payment {
    id: 'PAY-002',
    amount: 15000,
    date: date('2024-03-05'),
    method: 'bank_transfer',
    status: 'pending'
});

// Budgets
MERGE (b1:Budget {
    id: 'BUD-2024-Q1',
    period: 'Q1 2024',
    allocated: 500000,
    spent: 425000,
    variance: -75000,
    variance_pct: -15.0
})
MERGE (b2:Budget {
    id: 'BUD-2024-Q2',
    period: 'Q2 2024',
    allocated: 550000,
    spent: 480000,
    variance: -70000,
    variance_pct: -12.7
});

// Expenses
MERGE (e1:Expense {
    id: 'EXP-001',
    category: 'Software',
    amount: 10000,
    date: date('2024-02-12'),
    description: 'Monthly software licenses'
})
MERGE (e2:Expense {
    id: 'EXP-002',
    category: 'Marketing',
    amount: 15000,
    date: date('2024-02-15'),
    description: 'Ad campaign costs'
});

// ================================================================
// RELATIONSHIPS - Build the Financial Graph
// ================================================================

// Department owns Projects
MATCH (d1:Department {id: 'DEPT-001'}), (p1:Project {id: 'PROJ-001'})
MERGE (d1)-[:OWNS]->(p1);

MATCH (d2:Department {id: 'DEPT-002'}), (p2:Project {id: 'PROJ-002'})
MERGE (d2)-[:OWNS]->(p2);

MATCH (d3:Department {id: 'DEPT-003'}), (p3:Project {id: 'PROJ-003'})
MERGE (d3)-[:OWNS]->(p3);

// Contracts linked to Suppliers
MATCH (c1:Contract {id: 'CONT-001'}), (s1:Supplier {id: 'SUP-001'})
MERGE (c1)-[:WITH_SUPPLIER]->(s1);

MATCH (c2:Contract {id: 'CONT-002'}), (s2:Supplier {id: 'SUP-002'})
MERGE (c2)-[:WITH_SUPPLIER]->(s2);

MATCH (c3:Contract {id: 'CONT-003'}), (s3:Supplier {id: 'SUP-003'})
MERGE (c3)-[:WITH_SUPPLIER]->(s3);

// Invoices from Contracts
MATCH (i1:Invoice {id: 'INV-001'}), (c1:Contract {id: 'CONT-001'})
MERGE (i1)-[:FOR_CONTRACT]->(c1);

MATCH (i2:Invoice {id: 'INV-002'}), (c2:Contract {id: 'CONT-002'})
MERGE (i2)-[:FOR_CONTRACT]->(c2);

MATCH (i3:Invoice {id: 'INV-003'}), (c3:Contract {id: 'CONT-003'})
MERGE (i3)-[:FOR_CONTRACT]->(c3);

// Invoices from Suppliers
MATCH (i1:Invoice {id: 'INV-001'}), (s1:Supplier {id: 'SUP-001'})
MERGE (i1)-[:FROM_SUPPLIER]->(s1);

MATCH (i2:Invoice {id: 'INV-002'}), (s2:Supplier {id: 'SUP-002'})
MERGE (i2)-[:FROM_SUPPLIER]->(s2);

MATCH (i3:Invoice {id: 'INV-003'}), (s3:Supplier {id: 'SUP-003'})
MERGE (i3)-[:FROM_SUPPLIER]->(s3);

// Payments for Invoices
MATCH (pay1:Payment {id: 'PAY-001'}), (i1:Invoice {id: 'INV-001'})
MERGE (pay1)-[:FOR_INVOICE]->(i1);

// Expenses for Projects
MATCH (e1:Expense {id: 'EXP-001'}), (p2:Project {id: 'PROJ-002'})
MERGE (e1)-[:CHARGED_TO]->(p2);

MATCH (e2:Expense {id: 'EXP-002'}), (p1:Project {id: 'PROJ-001'})
MERGE (e2)-[:CHARGED_TO]->(p1);

// Budget for Departments
MATCH (b1:Budget {id: 'BUD-2024-Q1'}), (d1:Department {id: 'DEPT-001'})
MERGE (b1)-[:ALLOCATED_TO]->(d1);

// ================================================================
// EPISODIC MEMORY PATTERNS
// Add pattern nodes for recurring financial behaviors
// ================================================================

CREATE (pattern1:Pattern {
    id: 'PATTERN-001',
    type: 'late_payment',
    description: 'Supplier SUP-003 consistently pays late in Q4',
    confidence: 0.85,
    occurrences: 3,
    recommendation: 'Negotiate better terms or find alternative supplier'
});

MATCH (pattern1:Pattern {id: 'PATTERN-001'}), (s3:Supplier {id: 'SUP-003'})
MERGE (pattern1)-[:OBSERVED_IN]->(s3);

CREATE (pattern2:Pattern {
    id: 'PATTERN-002',
    type: 'budget_overrun',
    description: 'Marketing department consistently exceeds budget by 15%',
    confidence: 0.92,
    occurrences: 4,
    recommendation: 'Increase Marketing budget allocation or implement stricter controls'
});

MATCH (pattern2:Pattern {id: 'PATTERN-002'}), (d1:Department {id: 'DEPT-001'})
MERGE (pattern2)-[:OBSERVED_IN]->(d1);

// ================================================================
// RETURN SCHEMA SUMMARY
// ================================================================

MATCH (n)
RETURN labels(n) as NodeType, count(n) as Count
ORDER BY Count DESC;
