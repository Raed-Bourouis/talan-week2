// Financial Entity Graph Schema for Neo4j
// This schema defines the structure for financial relationships and episodic memory

// Create constraints and indexes
CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT department_id IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT budget_id IF NOT EXISTS FOR (b:Budget) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT payment_id IF NOT EXISTS FOR (p:Payment) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT client_id IF NOT EXISTS FOR (c:Client) REQUIRE c.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX budget_year IF NOT EXISTS FOR (b:Budget) ON (b.year);
CREATE INDEX contract_status IF NOT EXISTS FOR (c:Contract) ON (c.status);
CREATE INDEX invoice_status IF NOT EXISTS FOR (i:Invoice) ON (i.status);
CREATE INDEX payment_date IF NOT EXISTS FOR (p:Payment) ON (p.date);
CREATE INDEX supplier_name IF NOT EXISTS FOR (s:Supplier) ON (s.name);

// Sample Company Node
CREATE (company:Company {
  id: 'COMPANY001',
  name: 'Acme Financial Corp',
  industry: 'Financial Services',
  fiscal_year_start: '2024-01-01'
});

// Sample Department Nodes
CREATE (d1:Department {
  id: 'DEPT001',
  name: 'Marketing',
  head: 'John Smith',
  cost_center: 'CC-MKT-001'
}),
(d2:Department {
  id: 'DEPT002',
  name: 'R&D',
  head: 'Jane Doe',
  cost_center: 'CC-RD-001'
}),
(d3:Department {
  id: 'DEPT003',
  name: 'Operations',
  head: 'Bob Johnson',
  cost_center: 'CC-OPS-001'
});

// Sample Budget Nodes
CREATE (b1:Budget {
  id: 'BUDGET-2024-MKT',
  year: 2024,
  quarter: 'Q1',
  department_id: 'DEPT001',
  allocated_amount: 500000.00,
  spent_amount: 575000.00,
  variance: -75000.00,
  variance_percent: -0.15,
  status: 'over_budget',
  created_at: datetime('2024-01-01T00:00:00Z')
}),
(b2:Budget {
  id: 'BUDGET-2024-RD',
  year: 2024,
  quarter: 'Q1',
  department_id: 'DEPT002',
  allocated_amount: 800000.00,
  spent_amount: 720000.00,
  variance: 80000.00,
  variance_percent: 0.10,
  status: 'under_budget',
  created_at: datetime('2024-01-01T00:00:00Z')
});

// Sample Supplier Nodes
CREATE (s1:Supplier {
  id: 'SUPP001',
  name: 'TechVendor Inc',
  category: 'Technology',
  payment_terms: 'Net 30',
  risk_score: 0.2,
  reliability_score: 0.85
}),
(s2:Supplier {
  id: 'SUPP002',
  name: 'Office Solutions Ltd',
  category: 'Office Supplies',
  payment_terms: 'Net 45',
  risk_score: 0.1,
  reliability_score: 0.95
});

// Sample Contract Nodes
CREATE (c1:Contract {
  id: 'CONTRACT001',
  supplier_id: 'SUPP001',
  name: 'Annual Software License',
  start_date: date('2024-01-01'),
  end_date: date('2024-12-31'),
  value: 120000.00,
  status: 'active',
  auto_renew: true,
  payment_terms: 'Net 30',
  clauses: ['Auto-renewal', 'Price indexation +3%', 'SLA 99.9%']
}),
(c2:Contract {
  id: 'CONTRACT002',
  supplier_id: 'SUPP002',
  name: 'Office Supplies Framework',
  start_date: date('2024-01-01'),
  end_date: date('2024-06-30'),
  value: 50000.00,
  status: 'expiring_soon',
  auto_renew: false,
  payment_terms: 'Net 45',
  clauses: ['Volume discount', 'Quarterly review']
});

// Sample Invoice Nodes
CREATE (i1:Invoice {
  id: 'INV001',
  contract_id: 'CONTRACT001',
  supplier_id: 'SUPP001',
  invoice_number: 'INV-2024-001',
  amount: 10000.00,
  issue_date: date('2024-01-15'),
  due_date: date('2024-02-14'),
  payment_date: date('2024-02-20'),
  status: 'paid_late',
  days_late: 6,
  department_id: 'DEPT002'
}),
(i2:Invoice {
  id: 'INV002',
  contract_id: 'CONTRACT002',
  supplier_id: 'SUPP002',
  invoice_number: 'INV-2024-002',
  amount: 5000.00,
  issue_date: date('2024-01-20'),
  due_date: date('2024-03-06'),
  payment_date: null,
  status: 'pending',
  days_late: 0,
  department_id: 'DEPT003'
});

// Sample Payment Nodes
CREATE (p1:Payment {
  id: 'PAY001',
  invoice_id: 'INV001',
  amount: 10000.00,
  date: date('2024-02-20'),
  method: 'Wire Transfer',
  reference: 'WT-2024-001'
});

// Sample Client Node
CREATE (client1:Client {
  id: 'CLIENT001',
  name: 'Enterprise Customer',
  category: 'Enterprise',
  payment_reliability: 0.92,
  average_payment_delay: 5
});

// Create Relationships
MATCH (company:Company {id: 'COMPANY001'})
MATCH (d1:Department {id: 'DEPT001'})
MATCH (d2:Department {id: 'DEPT002'})
MATCH (d3:Department {id: 'DEPT003'})
CREATE (company)-[:HAS_DEPARTMENT]->(d1),
       (company)-[:HAS_DEPARTMENT]->(d2),
       (company)-[:HAS_DEPARTMENT]->(d3);

MATCH (d1:Department {id: 'DEPT001'})
MATCH (b1:Budget {id: 'BUDGET-2024-MKT'})
CREATE (d1)-[:HAS_BUDGET]->(b1);

MATCH (d2:Department {id: 'DEPT002'})
MATCH (b2:Budget {id: 'BUDGET-2024-RD'})
CREATE (d2)-[:HAS_BUDGET]->(b2);

MATCH (s1:Supplier {id: 'SUPP001'})
MATCH (c1:Contract {id: 'CONTRACT001'})
CREATE (s1)-[:HAS_CONTRACT]->(c1);

MATCH (s2:Supplier {id: 'SUPP002'})
MATCH (c2:Contract {id: 'CONTRACT002'})
CREATE (s2)-[:HAS_CONTRACT]->(c2);

MATCH (c1:Contract {id: 'CONTRACT001'})
MATCH (i1:Invoice {id: 'INV001'})
CREATE (c1)-[:GENERATED_INVOICE]->(i1);

MATCH (c2:Contract {id: 'CONTRACT002'})
MATCH (i2:Invoice {id: 'INV002'})
CREATE (c2)-[:GENERATED_INVOICE]->(i2);

MATCH (i1:Invoice {id: 'INV001'})
MATCH (p1:Payment {id: 'PAY001'})
CREATE (i1)-[:HAS_PAYMENT]->(p1);

MATCH (d2:Department {id: 'DEPT002'})
MATCH (i1:Invoice {id: 'INV001'})
CREATE (d2)-[:INCURRED_EXPENSE]->(i1);

MATCH (d3:Department {id: 'DEPT003'})
MATCH (i2:Invoice {id: 'INV002'})
CREATE (d3)-[:INCURRED_EXPENSE]->(i2);

// Create Episodic Memory Patterns
CREATE (pattern1:Pattern {
  id: 'PATTERN001',
  type: 'supplier_delay',
  description: 'TechVendor Inc consistently delivers late in Q4',
  confidence: 0.85,
  occurrences: 3,
  last_observed: datetime('2023-12-15T00:00:00Z'),
  recommendation: 'Add 2-week buffer for Q4 orders'
});

MATCH (s1:Supplier {id: 'SUPP001'})
MATCH (pattern1:Pattern {id: 'PATTERN001'})
CREATE (s1)-[:HAS_PATTERN]->(pattern1);

// Create anomaly detection
CREATE (anomaly1:Anomaly {
  id: 'ANOM001',
  type: 'duplicate_invoice',
  severity: 'high',
  description: 'Potential duplicate invoice detected',
  detected_at: datetime('2024-02-01T00:00:00Z'),
  status: 'resolved'
});

RETURN 'Schema initialized successfully' as status;
