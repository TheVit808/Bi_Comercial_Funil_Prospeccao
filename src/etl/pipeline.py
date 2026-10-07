import sqlite3
from datetime import datetime, timezone

def log_etl_execution():
    db_path = "data/bi_comercial.db"
    
    with sqlite3.connect(db_path) as con:
        con.execute("""
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
        """)
        
        con.execute(
            "INSERT INTO etl_load_log (load_id, source_system, table_name, load_type, started_at, finished_at, rows_read, rows_loaded, rows_rejected, watermark_start, watermark_end, status, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (None, "pipeline_comercial", "fact_revenue", "FULL", datetime.now(timezone.utc).isoformat(), None, 0, 0, 0, None, None, "STARTED", None)
        )
        con.commit()

if __name__ == "__main__":
    # ... etapas do seu ETL (extracao, transformacao, etc) ...
    
    # Chama o registro do log ao final do processo
    log_etl_execution()