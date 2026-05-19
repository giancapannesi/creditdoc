-- CreditDoc Regulatory Data Layer — Schema
-- Separate DB: regulator.db — zero changes to creditdoc.db

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Shared entity resolution
CREATE TABLE IF NOT EXISTS regulator_entities (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    creditdoc_slug TEXT,
    fdic_cert INTEGER,
    ncua_cu_number INTEGER,
    match_confidence REAL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    id INTEGER PRIMARY KEY,
    entity_id INTEGER REFERENCES regulator_entities(id),
    alias TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- CFPB Complaints
CREATE TABLE IF NOT EXISTS cfpb_complaints (
    complaint_id INTEGER PRIMARY KEY,
    date_received TEXT,
    product TEXT,
    sub_product TEXT,
    issue TEXT,
    sub_issue TEXT,
    company TEXT,
    company_normalized TEXT,
    state TEXT,
    consumer_consent_provided TEXT,
    submitted_via TEXT,
    date_sent_to_company TEXT,
    company_response TEXT,
    timely_response TEXT,
    consumer_disputed TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cfpb_company_stats (
    company_normalized TEXT PRIMARY KEY,
    total_complaints_alltime INTEGER,
    total_complaints_12mo INTEGER,
    total_complaints_3mo INTEGER,
    timely_response_rate REAL,
    resolved_with_relief_rate REAL,
    top_issue_1 TEXT,
    top_issue_1_pct REAL,
    top_issue_2 TEXT,
    top_issue_2_pct REAL,
    top_issue_3 TEXT,
    top_issue_3_pct REAL,
    complaint_trend TEXT,
    last_computed TEXT
);

-- CFPB Enforcement
CREATE TABLE IF NOT EXISTS cfpb_enforcement_actions (
    id INTEGER PRIMARY KEY,
    company TEXT,
    company_normalized TEXT,
    title TEXT,
    action_date TEXT,
    penalty_amount REAL,
    description TEXT,
    case_url TEXT,
    status TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- FDIC
CREATE TABLE IF NOT EXISTS fdic_institutions (
    cert INTEGER PRIMARY KEY,
    institution_name TEXT,
    city TEXT,
    state TEXT,
    active INTEGER,
    website TEXT,
    class TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fdic_locations (
    id INTEGER PRIMARY KEY,
    cert INTEGER REFERENCES fdic_institutions(cert),
    branch_name TEXT,
    city TEXT,
    state TEXT,
    county TEXT,
    address TEXT,
    zip TEXT,
    latitude REAL,
    longitude REAL,
    main_office INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

-- SBA
CREATE TABLE IF NOT EXISTS sba_loans (
    id INTEGER PRIMARY KEY,
    program TEXT,
    lender_name TEXT,
    lender_name_normalized TEXT,
    lender_city TEXT,
    lender_state TEXT,
    borrower_state TEXT,
    approval_date TEXT,
    gross_approval REAL,
    sba_guaranteed REAL,
    fiscal_year INTEGER,
    naics_code TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sba_lender_state_year (
    lender_name_normalized TEXT,
    state TEXT,
    fiscal_year INTEGER,
    program TEXT,
    loan_count INTEGER,
    total_approval REAL,
    total_sba_guaranteed REAL,
    rank_state INTEGER,
    PRIMARY KEY (lender_name_normalized, state, fiscal_year, program)
);

CREATE TABLE IF NOT EXISTS sba_lender_national_year (
    lender_name_normalized TEXT,
    fiscal_year INTEGER,
    program TEXT,
    loan_count INTEGER,
    total_approval REAL,
    total_sba_guaranteed REAL,
    rank_national INTEGER,
    PRIMARY KEY (lender_name_normalized, fiscal_year, program)
);

-- Pipeline tracking
CREATE TABLE IF NOT EXISTS ingest_runs (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    records_fetched INTEGER,
    records_inserted INTEGER,
    records_updated INTEGER,
    status TEXT,
    error_message TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cfpb_complaints_company ON cfpb_complaints(company_normalized);
CREATE INDEX IF NOT EXISTS idx_cfpb_complaints_date ON cfpb_complaints(date_received);
CREATE INDEX IF NOT EXISTS idx_cfpb_enforcement_company ON cfpb_enforcement_actions(company_normalized);
CREATE INDEX IF NOT EXISTS idx_fdic_locations_state_city ON fdic_locations(state, city);
CREATE INDEX IF NOT EXISTS idx_fdic_locations_cert ON fdic_locations(cert);
CREATE INDEX IF NOT EXISTS idx_sba_loans_lender ON sba_loans(lender_name_normalized);
CREATE INDEX IF NOT EXISTS idx_sba_loans_state ON sba_loans(borrower_state);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_alias ON entity_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_regulator_entities_slug ON regulator_entities(creditdoc_slug);
CREATE INDEX IF NOT EXISTS idx_regulator_entities_norm ON regulator_entities(normalized_name);
