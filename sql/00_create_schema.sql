PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS etl_load_log (
    load_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system TEXT NOT NULL,
    table_name TEXT NOT NULL,
    load_type TEXT NOT NULL CHECK (load_type IN ('FULL', 'INCREMENTAL')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    rows_read INTEGER DEFAULT 0,
    rows_loaded INTEGER DEFAULT 0,
    rows_rejected INTEGER DEFAULT 0,
    watermark_start TEXT,
    watermark_end TEXT,
    status TEXT NOT NULL CHECK (status IN ('STARTED', 'SUCCESS', 'ERROR')),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS dim_channel (
    channel_key INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE,
    channel_group TEXT NOT NULL,
    planned_cac_brl NUMERIC NOT NULL CHECK (planned_cac_brl >= 0)
);

CREATE TABLE IF NOT EXISTS dim_sales_rep (
    sales_rep_key INTEGER PRIMARY KEY,
    sales_rep_name TEXT NOT NULL,
    region TEXT NOT NULL,
    team TEXT NOT NULL,
    hire_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_start TEXT NOT NULL,
    week_of_year INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

CREATE TABLE IF NOT EXISTS dim_lead (
    lead_key INTEGER PRIMARY KEY,
    lead_business_id TEXT NOT NULL UNIQUE,
    created_date TEXT NOT NULL,
    created_date_key INTEGER NOT NULL,
    channel_key INTEGER NOT NULL,
    sales_rep_key INTEGER NOT NULL,
    region TEXT NOT NULL,
    segment TEXT NOT NULL,
    industry TEXT NOT NULL,
    quality_score NUMERIC NOT NULL CHECK (quality_score BETWEEN 0 AND 1),
    mql_flag INTEGER NOT NULL CHECK (mql_flag IN (0, 1)),
    sql_flag INTEGER NOT NULL CHECK (sql_flag IN (0, 1)),
    opportunity_flag INTEGER NOT NULL CHECK (opportunity_flag IN (0, 1)),
    mql_date TEXT,
    sql_date TEXT,
    opportunity_date TEXT,
    current_stage TEXT NOT NULL,
    FOREIGN KEY (created_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key),
    FOREIGN KEY (sales_rep_key) REFERENCES dim_sales_rep(sales_rep_key)
);

CREATE TABLE IF NOT EXISTS fact_interaction (
    interaction_key INTEGER PRIMARY KEY,
    lead_key INTEGER NOT NULL,
    sales_rep_key INTEGER NOT NULL,
    channel_key INTEGER NOT NULL,
    interaction_date TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    outcome TEXT NOT NULL,
    duration_minutes NUMERIC NOT NULL CHECK (duration_minutes >= 0),
    is_completed INTEGER NOT NULL CHECK (is_completed IN (0, 1)),
    source_system TEXT NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0,
    anomaly_type TEXT,
    FOREIGN KEY (lead_key) REFERENCES dim_lead(lead_key),
    FOREIGN KEY (sales_rep_key) REFERENCES dim_sales_rep(sales_rep_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key)
);

CREATE INDEX IF NOT EXISTS ix_interaction_date ON fact_interaction(interaction_date);
CREATE INDEX IF NOT EXISTS ix_interaction_lead ON fact_interaction(lead_key);