"""
F360 – Générateur de Données Synthétiques
=========================================
Produit des CSV réalistes pour alimenter toutes les tables F360.

Données DÉJÀ DISPONIBLES dans Input/ (non re-générées) :
  - 30 PDF contrats financement auto  (Contract_1..30.pdf)
  - contracts.csv  : 1.3M lignes jobs freelance (job_id, title, dates, hours, paid, rate)
  - CUAD_v1/       : 510 contrats annotés (clauses, parties, dates) + PDFs + TXT

Ce script COMPLÈTE avec les données manquantes :
  ✅ companies.csv          – 5 entreprises
  ✅ departments.csv        – 25 départements (5 par entreprise)
  ✅ counterparties.csv     – 60 fournisseurs & clients
  ✅ contracts_structured.csv – 80 contrats structurés (ref, montants, clauses)
  ✅ invoices.csv           – 500 factures
  ✅ budgets.csv            – 75 lignes budgétaires (3 ans × 5 cat × 5 entreprises)
  ✅ accounting_entries.csv – 1000 écritures comptables
  ✅ cashflow_entries.csv   – 730 mouvements de trésorerie (2 ans)
  ✅ seed.sql               – INSERT SQL prêt à charger dans PostgreSQL

Usage :
    cd Input
    python generate_synthetic_data.py
"""
from __future__ import annotations

import csv
import math
import os
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────
random.seed(42)
OUTPUT_DIR = Path(__file__).parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

SEED_SQL_PATH = Path(__file__).parent / "generated" / "seed.sql"

# ── Helpers ─────────────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))

def money(low: float, high: float) -> Decimal:
    return Decimal(str(round(random.uniform(low, high), 2)))

def write_csv(filename: str, rows: list[dict], fieldnames: list[str]):
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ {filename} → {len(rows)} rows")
    return path

def sql_val(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float, Decimal)):
        return str(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"

# ── Reference data ─────────────────────────────────────────────

COMPANY_DATA = [
    {"name": "Talan Group",      "siren": "532456789", "sector": "Consulting",    "country": "France"},
    {"name": "FinServ SA",       "siren": "412345678", "sector": "Financial Services", "country": "France"},
    {"name": "Nextera Industries","siren": "698765432", "sector": "Manufacturing", "country": "France"},
    {"name": "DigiPay Europe",   "siren": "753159852", "sector": "Fintech",       "country": "France"},
    {"name": "GreenLogistics SAS","siren": "321654987", "sector": "Logistics",    "country": "France"},
]

DEPT_NAMES = ["Finance", "IT / DSI", "Ressources Humaines", "Marketing", "Achats"]

SUPPLIER_NAMES = [
    "Capgemini", "Accenture", "Sopra Steria", "Atos", "IBM France",
    "Microsoft France", "OVHcloud", "Salesforce EU", "SAP France", "Oracle France",
    "Orange Business", "SFR Business", "Bouygues Telecom Pro", "Dell Technologies",
    "HP Enterprise", "Lenovo France", "Thales DIS", "Schneider Electric",
    "Dassault Systèmes", "Sodexo", "Edenred", "Bureau Veritas",
    "Euler Hermes", "AXA Corporate", "Generali France", "KPMG France",
    "Deloitte France", "EY France", "PwC France", "BDO France",
]

CLIENT_NAMES = [
    "LVMH", "TotalEnergies", "L'Oréal", "BNP Paribas", "Société Générale",
    "Crédit Agricole", "AXA Group", "Engie", "Danone", "Pernod Ricard",
    "Renault Group", "PSA Stellantis", "Air France-KLM", "Saint-Gobain",
    "Carrefour", "Publicis Groupe", "Vivendi", "Veolia", "Legrand",
    "Worldline", "Atos Group", "Kering", "Hermès International",
    "Schneider SE", "Michelin", "Safran", "Airbus SE", "Thales Group",
    "Bouygues SA", "Vinci SA",
]

CONTRACT_TYPES = ["service", "supply", "lease", "consulting"]
CONTRACT_TITLES_SERVICE = [
    "Maintenance applicative ERP", "Support infrastructure cloud",
    "Audit sécurité SI", "Développement plateforme web",
    "Formation management agile", "Conseil transformation digitale",
    "Maintenance réseau & télécom", "Support utilisateurs N1/N2",
]
CONTRACT_TITLES_SUPPLY = [
    "Fourniture postes de travail", "Licences logicielles annuelles",
    "Équipement datacenter", "Matériel réseau switches & routeurs",
    "Fourniture mobilier de bureau", "Papeterie & consommables",
]
CONTRACT_TITLES_LEASE = [
    "Location bureaux Paris 8e", "Leasing flotte automobile",
    "Location serveurs dédiés", "Bail entrepôt logistique Roissy",
]
CONTRACT_TITLES_CONSULTING = [
    "Mission conseil stratégique", "Accompagnement mise en conformité RGPD",
    "Étude de marché Europe du Sud", "Due diligence acquisition cible",
    "Optimisation processus financiers", "Benchmark concurrentiel secteur",
]

BUDGET_CATEGORIES = ["OPEX", "CAPEX", "HR", "IT", "Marketing"]
PAYMENT_TERMS = ["30 jours net", "45 jours fin de mois", "60 jours net", "Paiement à réception"]
PENALTY_CLAUSES = [
    "Pénalité de retard : 1.5% par semaine de retard",
    "Indemnité forfaitaire de 5 000 EUR en cas de non-respect SLA",
    "Clause de bonus/malus selon indicateurs qualité trimestriels",
    "Pénalité de 2% du montant mensuel par jour de retard au-delà de 5 jours ouvrés",
    None,
]
INDEXATION_CLAUSES = [
    "Indexation annuelle sur l'indice Syntec",
    "Révision annuelle sur indice INSEE des prix à la consommation",
    "Indexation sur indice ILAT (Indice des Loyers des Activités Tertiaires)",
    "Prix fixe pendant la durée du contrat",
    None,
]

JOURNAL_CODES = ["ACH", "VTE", "BQ1", "BQ2", "OD", "AN"]
ACCOUNT_MAP = {
    "ACH": [("601000", "Achats matières premières"), ("602000", "Achats sous-traitance"),
             ("604000", "Achats études & prestations"), ("606000", "Achats non stockés")],
    "VTE": [("701000", "Ventes produits finis"), ("706000", "Prestations de services"),
             ("707000", "Ventes marchandises")],
    "BQ1": [("512000", "Banque – compte courant"), ("530000", "Caisse")],
    "BQ2": [("512100", "Banque – compte épargne"), ("164000", "Emprunts")],
    "OD":  [("658000", "Charges diverses gestion"), ("681000", "Dotations amort.")],
    "AN":  [("120000", "Résultat exercice"), ("101000", "Capital social")],
}

CASHFLOW_CATEGORIES_IN = ["Règlement client", "Subvention", "Apport capital", "Intérêts reçus", "Vente actif"]
CASHFLOW_CATEGORIES_OUT = [
    "Paiement fournisseur", "Salaires", "Loyer", "Charges sociales",
    "Abonnements SaaS", "Impôts & taxes", "Remboursement emprunt",
    "Achat matériel", "Frais déplacement", "Honoraires conseil",
]


# ══════════════════════════════════════════════════════════════
# GENERATION FUNCTIONS
# ══════════════════════════════════════════════════════════════

def gen_companies() -> list[dict]:
    rows = []
    for c in COMPANY_DATA:
        rows.append({"id": uid(), **c, "created_at": "2024-01-01"})
    return rows


def gen_departments(companies: list[dict]) -> list[dict]:
    rows = []
    for comp in companies:
        for i, dept_name in enumerate(DEPT_NAMES):
            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "name": dept_name,
                "code": dept_name.split(" ")[0].upper()[:3],
                "created_at": "2024-01-01",
            })
    return rows


def gen_counterparties(companies: list[dict]) -> list[dict]:
    rows = []
    for comp in companies:
        # 6 fournisseurs par entreprise
        for name in random.sample(SUPPLIER_NAMES, 6):
            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "name": name,
                "type": "supplier",
                "tax_id": f"FR{random.randint(10,99)}{random.randint(100000000,999999999)}",
                "contact_email": f"contact@{name.lower().replace(' ', '').replace('/', '')}.fr",
                "created_at": "2024-01-01",
            })
        # 6 clients par entreprise
        for name in random.sample(CLIENT_NAMES, 6):
            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "name": name,
                "type": "client",
                "tax_id": f"FR{random.randint(10,99)}{random.randint(100000000,999999999)}",
                "contact_email": f"finance@{name.lower().replace(' ', '').replace('/', '').replace('-', '').replace(chr(39), '')}.com",
                "created_at": "2024-01-01",
            })
    return rows


def gen_contracts(companies, departments, counterparties) -> list[dict]:
    rows = []
    ref_counter = 1

    suppliers = [c for c in counterparties if c["type"] == "supplier"]
    for comp in companies:
        comp_suppliers = [s for s in suppliers if s["company_id"] == comp["id"]]
        comp_depts = [d for d in departments if d["company_id"] == comp["id"]]

        for _ in range(16):  # 16 contrats par entreprise = 80 total
            ct = random.choice(CONTRACT_TYPES)
            if ct == "service":
                title = random.choice(CONTRACT_TITLES_SERVICE)
            elif ct == "supply":
                title = random.choice(CONTRACT_TITLES_SUPPLY)
            elif ct == "lease":
                title = random.choice(CONTRACT_TITLES_LEASE)
            else:
                title = random.choice(CONTRACT_TITLES_CONSULTING)

            start = rand_date(date(2022, 1, 1), date(2025, 6, 1))
            duration_months = random.choice([6, 12, 24, 36, 48])
            end = start + timedelta(days=duration_months * 30)
            amount = money(5_000, 2_500_000)
            status = "active" if end >= date.today() else "expired"

            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "counterparty_id": random.choice(comp_suppliers)["id"],
                "department_id": random.choice(comp_depts)["id"],
                "reference": f"CTR-{comp['name'][:3].upper()}-{ref_counter:04d}",
                "title": title,
                "contract_type": ct,
                "start_date": str(start),
                "end_date": str(end),
                "total_amount": str(amount),
                "currency": "EUR",
                "payment_terms": random.choice(PAYMENT_TERMS),
                "penalty_clauses": random.choice(PENALTY_CLAUSES),
                "indexation_clause": random.choice(INDEXATION_CLAUSES),
                "status": status,
                "created_at": str(start),
            })
            ref_counter += 1

    return rows


def gen_invoices(companies, contracts, counterparties) -> list[dict]:
    rows = []
    inv_counter = 1

    for comp in companies:
        comp_contracts = [c for c in contracts if c["company_id"] == comp["id"]]
        comp_clients = [c for c in counterparties if c["company_id"] == comp["id"] and c["type"] == "client"]
        comp_suppliers = [c for c in counterparties if c["company_id"] == comp["id"] and c["type"] == "supplier"]

        # Factures liées à des contrats (sortantes = paiements fournisseurs)
        for contract in comp_contracts:
            n_invoices = random.randint(1, 6)
            contract_total = Decimal(contract["total_amount"])
            for j in range(n_invoices):
                inv_date = rand_date(
                    date.fromisoformat(contract["start_date"]),
                    min(date.fromisoformat(contract["end_date"]), date.today()),
                )
                amount_ht = (contract_total / n_invoices).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax = (amount_ht * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ttc = amount_ht + tax
                due = inv_date + timedelta(days=random.choice([30, 45, 60]))
                is_overdue = due < date.today() and random.random() < 0.15
                is_paid = due < date.today() and not is_overdue and random.random() < 0.85
                status = "overdue" if is_overdue else ("paid" if is_paid else "pending")

                rows.append({
                    "id": uid(),
                    "company_id": comp["id"],
                    "contract_id": contract["id"],
                    "counterparty_id": contract["counterparty_id"],
                    "invoice_number": f"FA-{inv_counter:06d}",
                    "invoice_date": str(inv_date),
                    "due_date": str(due),
                    "amount_ht": str(amount_ht),
                    "amount_tax": str(tax),
                    "amount_ttc": str(ttc),
                    "currency": "EUR",
                    "status": status,
                    "direction": "outbound",
                    "created_at": str(inv_date),
                })
                inv_counter += 1

        # Factures clients (entrantes)
        for _ in range(20):
            client = random.choice(comp_clients)
            inv_date = rand_date(date(2023, 1, 1), date.today())
            amount_ht = money(2_000, 500_000)
            tax = (amount_ht * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ttc = amount_ht + tax
            due = inv_date + timedelta(days=random.choice([30, 45, 60]))
            status = "paid" if due < date.today() and random.random() < 0.80 else "pending"

            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "contract_id": None,
                "counterparty_id": client["id"],
                "invoice_number": f"FC-{inv_counter:06d}",
                "invoice_date": str(inv_date),
                "due_date": str(due),
                "amount_ht": str(amount_ht),
                "amount_tax": str(tax),
                "amount_ttc": str(ttc),
                "currency": "EUR",
                "status": status,
                "direction": "inbound",
                "created_at": str(inv_date),
            })
            inv_counter += 1

    return rows


def gen_budgets(companies, departments) -> list[dict]:
    rows = []
    for comp in companies:
        comp_depts = [d for d in departments if d["company_id"] == comp["id"]]
        for year in [2024, 2025, 2026]:
            for cat in BUDGET_CATEGORIES:
                dept = random.choice(comp_depts)
                planned = money(100_000, 3_000_000)
                # Actual = planned ± 5-25%
                deviation = random.uniform(-0.25, 0.15)
                actual = (planned * (1 + Decimal(str(deviation)))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if year == 2026:
                    actual = Decimal("0")  # future year = no actual yet

                rows.append({
                    "id": uid(),
                    "company_id": comp["id"],
                    "department_id": dept["id"],
                    "fiscal_year": year,
                    "category": cat,
                    "planned_amount": str(planned),
                    "actual_amount": str(actual),
                    "currency": "EUR",
                    "created_at": f"{year}-01-01",
                })
    return rows


def gen_accounting_entries(companies, invoices) -> list[dict]:
    rows = []
    paid_invoices = [i for i in invoices if i["status"] == "paid"]

    for comp in companies:
        comp_invoices = [i for i in paid_invoices if i["company_id"] == comp["id"]]
        for inv in random.sample(comp_invoices, min(len(comp_invoices), 100)):
            journal = "ACH" if inv["direction"] == "outbound" else "VTE"
            accounts = ACCOUNT_MAP[journal]
            acct = random.choice(accounts)
            amount = Decimal(inv["amount_ttc"])
            e_date = date.fromisoformat(inv["invoice_date"]) + timedelta(days=random.randint(0, 30))

            # Double entry : debit & credit
            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "invoice_id": inv["id"],
                "entry_date": str(e_date),
                "journal_code": journal,
                "account_number": acct[0],
                "label": f"{acct[1]} – {inv['invoice_number']}",
                "debit": str(amount) if journal == "ACH" else "0",
                "credit": "0" if journal == "ACH" else str(amount),
                "created_at": str(e_date),
            })
            # Counter entry (banque)
            bank_acct = random.choice(ACCOUNT_MAP["BQ1"])
            rows.append({
                "id": uid(),
                "company_id": comp["id"],
                "invoice_id": inv["id"],
                "entry_date": str(e_date),
                "journal_code": "BQ1",
                "account_number": bank_acct[0],
                "label": f"{bank_acct[1]} – {inv['invoice_number']}",
                "debit": "0" if journal == "ACH" else str(amount),
                "credit": str(amount) if journal == "ACH" else "0",
                "created_at": str(e_date),
            })

    return rows


def gen_cashflow(companies) -> list[dict]:
    rows = []
    start = date(2024, 1, 1)
    end = date(2025, 12, 31)
    delta = (end - start).days

    for comp in companies:
        for day_offset in range(delta + 1):
            d = start + timedelta(days=day_offset)
            if d.weekday() >= 5:  # pas le week-end (ou très peu)
                if random.random() > 0.05:
                    continue

            # Entrées (in)
            if random.random() < 0.6:  # 60% des jours ont un encaissement
                cat = random.choice(CASHFLOW_CATEGORIES_IN)
                amount = money(500, 150_000)
                rows.append({
                    "id": uid(),
                    "company_id": comp["id"],
                    "entry_date": str(d),
                    "amount": str(amount),
                    "direction": "in",
                    "category": cat,
                    "source": "invoice" if "client" in cat.lower() else "manual",
                    "is_projected": str(d > date.today()).upper(),
                    "created_at": str(d),
                })

            # Sorties (out) 
            if random.random() < 0.75:  # 75% des jours ont un décaissement
                cat = random.choice(CASHFLOW_CATEGORIES_OUT)
                amount = money(200, 80_000)
                rows.append({
                    "id": uid(),
                    "company_id": comp["id"],
                    "entry_date": str(d),
                    "amount": str(amount),
                    "direction": "out",
                    "category": cat,
                    "source": "invoice" if "fournisseur" in cat.lower() else "manual",
                    "is_projected": str(d > date.today()).upper(),
                    "created_at": str(d),
                })

    return rows


# ══════════════════════════════════════════════════════════════
# SQL SEED GENERATOR
# ══════════════════════════════════════════════════════════════

def gen_insert(table: str, rows: list[dict], skip_cols: list[str] | None = None) -> str:
    if not rows:
        return ""
    skip = set(skip_cols or [])
    cols = [c for c in rows[0].keys() if c not in skip]
    lines = [f"\n-- {table} ({len(rows)} rows)"]
    lines.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")

    value_rows = []
    for r in rows:
        vals = ", ".join(sql_val(r.get(c)) for c in cols)
        value_rows.append(f"  ({vals})")

    lines.append(",\n".join(value_rows) + ";")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("🚀 F360 – Generating synthetic data...\n")

    # ── Generate all datasets ───────────────────
    companies = gen_companies()
    write_csv("companies.csv", companies,
              ["id", "name", "siren", "sector", "country", "created_at"])

    departments = gen_departments(companies)
    write_csv("departments.csv", departments,
              ["id", "company_id", "name", "code", "created_at"])

    counterparties = gen_counterparties(companies)
    write_csv("counterparties.csv", counterparties,
              ["id", "company_id", "name", "type", "tax_id", "contact_email", "created_at"])

    contracts = gen_contracts(companies, departments, counterparties)
    write_csv("contracts_structured.csv", contracts,
              ["id", "company_id", "counterparty_id", "department_id", "reference",
               "title", "contract_type", "start_date", "end_date", "total_amount",
               "currency", "payment_terms", "penalty_clauses", "indexation_clause",
               "status", "created_at"])

    invoices = gen_invoices(companies, contracts, counterparties)
    write_csv("invoices.csv", invoices,
              ["id", "company_id", "contract_id", "counterparty_id", "invoice_number",
               "invoice_date", "due_date", "amount_ht", "amount_tax", "amount_ttc",
               "currency", "status", "direction", "created_at"])

    budgets = gen_budgets(companies, departments)
    write_csv("budgets.csv", budgets,
              ["id", "company_id", "department_id", "fiscal_year", "category",
               "planned_amount", "actual_amount", "currency", "created_at"])

    accounting = gen_accounting_entries(companies, invoices)
    write_csv("accounting_entries.csv", accounting,
              ["id", "company_id", "invoice_id", "entry_date", "journal_code",
               "account_number", "label", "debit", "credit", "created_at"])

    cashflow = gen_cashflow(companies)
    write_csv("cashflow_entries.csv", cashflow,
              ["id", "company_id", "entry_date", "amount", "direction",
               "category", "source", "is_projected", "created_at"])

    # ── Generate SQL seed ───────────────────────
    print("\n📝 Generating seed.sql...")
    sql_parts = [
        "-- ============================================================",
        "-- F360 – Synthetic Seed Data",
        f"-- Generated: {datetime.now().isoformat()}",
        "-- ============================================================",
        "",
        "BEGIN;",
        gen_insert("companies", companies),
        gen_insert("departments", departments),
        gen_insert("counterparties", counterparties),
        gen_insert("contracts", contracts),
        gen_insert("invoices", invoices),
        gen_insert("budgets", budgets),
        gen_insert("accounting_entries", accounting),
        gen_insert("cashflow_entries", cashflow),
        "",
        "COMMIT;",
    ]
    with open(SEED_SQL_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_parts))
    print(f"  ✅ seed.sql written")

    # ── Summary ─────────────────────────────────
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  F360 Synthetic Data Generation – COMPLETE                   ║
╠══════════════════════════════════════════════════════════════╣
║  Companies:           {len(companies):>6}                              ║
║  Departments:         {len(departments):>6}                              ║
║  Counterparties:      {len(counterparties):>6}                              ║
║  Contracts:           {len(contracts):>6}                              ║
║  Invoices:            {len(invoices):>6}                              ║
║  Budgets:             {len(budgets):>6}                              ║
║  Accounting entries:  {len(accounting):>6}                              ║
║  Cashflow entries:    {len(cashflow):>6}                              ║
╠══════════════════════════════════════════════════════════════╣
║  Output: Input/generated/                                    ║
║  SQL:    Input/generated/seed.sql                            ║
╠══════════════════════════════════════════════════════════════╣
║  EXISTING DATA (not regenerated):                            ║
║  • 30 PDF contrats (Contract_1..30.pdf)                      ║
║  • contracts.csv – 1.3M lignes jobs freelance                ║
║  • CUAD_v1/ – 510 contrats annotés + clauses                 ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
