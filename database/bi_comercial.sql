PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS etl_load_log (
    load_log_key INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name TEXT NOT NULL,
    source_system TEXT NOT NULL,
    source_file TEXT,
    target_table TEXT NOT NULL,
    load_type TEXT NOT NULL CHECK (load_type IN ('FULL', 'INCREMENTAL')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    rows_read INTEGER DEFAULT 0,
    rows_inserted INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    rows_rejected INTEGER DEFAULT 0,
    watermark_before TEXT,
    watermark_after TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS etl_rejection_log (
    rejection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    load_log_key INTEGER NOT NULL,
    source_system TEXT NOT NULL,
    table_name TEXT NOT NULL,
    business_key TEXT,
    reason TEXT NOT NULL,
    raw_payload TEXT,
    rejected_at TEXT NOT NULL,
    FOREIGN KEY (load_log_key) REFERENCES etl_load_log(load_log_key)
);

CREATE TABLE IF NOT EXISTS stg_lead (
    load_log_key INTEGER NOT NULL,
    lead_id_business TEXT NOT NULL,
    created_date TEXT,
    channel_name TEXT,
    sales_rep_name TEXT,
    region TEXT,
    segment TEXT,
    company_size_employees INTEGER,
    lead_score INTEGER,
    is_mql INTEGER,
    is_sql INTEGER,
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    row_hash TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    FOREIGN KEY (load_log_key) REFERENCES etl_load_log(load_log_key)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    week_of_year INTEGER,
    day_of_week INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1)),
    month_start TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_channel (
    channel_key INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE,
    channel_group TEXT NOT NULL,
    share REAL NOT NULL CHECK (share >= 0),
    base_conversion REAL NOT NULL CHECK (base_conversion BETWEEN 0 AND 1),
    base_quality REAL NOT NULL CHECK (base_quality BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS dim_sales_rep (
    sales_rep_key INTEGER PRIMARY KEY,
    sales_rep_name TEXT NOT NULL,
    region TEXT NOT NULL,
    seniority TEXT NOT NULL,
    hire_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_lead (
    lead_key INTEGER PRIMARY KEY,
    lead_id_business TEXT NOT NULL UNIQUE,
    created_date TEXT NOT NULL,
    created_date_key INTEGER NOT NULL,
    channel_key INTEGER NOT NULL,
    sales_rep_key INTEGER NOT NULL,
    region TEXT NOT NULL,
    segment TEXT NOT NULL,
    company_size_employees INTEGER NOT NULL CHECK (company_size_employees > 0),
    lead_score INTEGER NOT NULL CHECK (lead_score BETWEEN 1 AND 99),
    is_mql INTEGER NOT NULL CHECK (is_mql IN (0, 1)),
    is_sql INTEGER NOT NULL CHECK (is_sql IN (0, 1)),
    source_system TEXT NOT NULL,
    is_test_record INTEGER NOT NULL DEFAULT 0 CHECK (is_test_record IN (0, 1)),
    anomaly_flag INTEGER NOT NULL DEFAULT 0 CHECK (anomaly_flag IN (0, 1)),
    FOREIGN KEY (created_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key),
    FOREIGN KEY (sales_rep_key) REFERENCES dim_sales_rep(sales_rep_key),
    CHECK (is_sql = 0 OR is_mql = 1)
);

CREATE TABLE IF NOT EXISTS fact_interaction (
    interaction_key INTEGER PRIMARY KEY,
    lead_key INTEGER NOT NULL,
    sales_rep_key INTEGER NOT NULL,
    channel_key INTEGER NOT NULL,
    interaction_date TEXT NOT NULL,
    interaction_date_key INTEGER NOT NULL,
    interaction_type TEXT NOT NULL,
    outcome TEXT NOT NULL,
    response_time_hours REAL NOT NULL CHECK (response_time_hours >= 0),
    source_system TEXT NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0 CHECK (anomaly_flag IN (0, 1)),
    FOREIGN KEY (lead_key) REFERENCES dim_lead(lead_key),
    FOREIGN KEY (sales_rep_key) REFERENCES dim_sales_rep(sales_rep_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key),
    FOREIGN KEY (interaction_date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE IF NOT EXISTS fact_opportunity (
    opportunity_key INTEGER PRIMARY KEY,
    opportunity_id_business TEXT NOT NULL UNIQUE,
    lead_key INTEGER NOT NULL,
    sales_rep_key INTEGER NOT NULL,
    channel_key INTEGER NOT NULL,
    created_date TEXT NOT NULL,
    created_date_key INTEGER NOT NULL,
    close_date TEXT,
    close_date_key INTEGER,
    status TEXT NOT NULL CHECK (status IN ('Won', 'Lost', 'Open')),
    estimated_value_brl REAL NOT NULL CHECK (estimated_value_brl >= 0),
    discount_pct REAL NOT NULL CHECK (discount_pct BETWEEN 0 AND 1),
    won_value_brl REAL NOT NULL CHECK (won_value_brl >= 0),
    sales_cycle_days REAL NOT NULL CHECK (sales_cycle_days >= 0),
    source_system TEXT NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0 CHECK (anomaly_flag IN (0, 1)),
    FOREIGN KEY (lead_key) REFERENCES dim_lead(lead_key),
    FOREIGN KEY (sales_rep_key) REFERENCES dim_sales_rep(sales_rep_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key),
    FOREIGN KEY (created_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (close_date_key) REFERENCES dim_date(date_key),
    CHECK ((status = 'Won' AND won_value_brl > 0 AND close_date IS NOT NULL) OR (status <> 'Won' AND won_value_brl = 0))
);

CREATE TABLE IF NOT EXISTS fact_revenue (
    revenue_key INTEGER PRIMARY KEY,
    opportunity_key INTEGER NOT NULL UNIQUE,
    lead_key INTEGER NOT NULL,
    sales_rep_key INTEGER NOT NULL,
    channel_key INTEGER NOT NULL,
    revenue_date TEXT NOT NULL,
    revenue_date_key INTEGER NOT NULL,
    revenue_type TEXT NOT NULL,
    amount_brl REAL NOT NULL CHECK (amount_brl > 0),
    is_recurring INTEGER NOT NULL CHECK (is_recurring IN (0, 1)),
    source_system TEXT NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0 CHECK (anomaly_flag IN (0, 1)),
    FOREIGN KEY (opportunity_key) REFERENCES fact_opportunity(opportunity_key),
    FOREIGN KEY (lead_key) REFERENCES dim_lead(lead_key),
    FOREIGN KEY (sales_rep_key) REFERENCES dim_sales_rep(sales_rep_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key),
    FOREIGN KEY (revenue_date_key) REFERENCES dim_date(date_key)
);