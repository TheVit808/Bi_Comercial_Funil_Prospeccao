import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

# Definindo caminhos de forma dinâmica em relação à raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "bi_comercial.db"
SAMPLE_DIR = BASE_DIR / "data" / "sample"


def init_db_schema(con: sqlite3.Connection):
    """Garante a existência da tabela de controle de auditoria."""
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


def run_pipeline():
    started_at = datetime.now(timezone.utc).isoformat()
    
    # Mapeamento dos arquivos de origem para as tabelas do SQLite
    datasets = {
        "dim_lead": SAMPLE_DIR / "dim_lead.parquet",
        "fact_revenue": SAMPLE_DIR / "fact_revenue.parquet",
        "fact_interaction": SAMPLE_DIR / "fact_interaction.parquet",
        "fact_opportunity": SAMPLE_DIR / "fact_opportunity.parquet",  # Adicionado
    }
    
    # Garantir que a pasta data/ existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as con:
        init_db_schema(con)
        
        # Registra início da execução
        cursor = con.cursor()
        cursor.execute(
            """
            INSERT INTO etl_load_log 
            (source_system, table_name, load_type, started_at, status) 
            VALUES (?, ?, ?, ?, ?)
            """,
            ("pipeline_comercial", "all_tables", "FULL", started_at, "STARTED")
        )
        load_id = cursor.lastrowid
        con.commit()
        
        try:
            total_loaded = 0
            
            # Carga física dos DataFrames nas tabelas do SQLite
            for table_name, file_path in datasets.items():
                if file_path.exists():
                    df = pd.read_parquet(file_path)
                    df.to_sql(table_name, con, if_exists="replace", index=False)
                    total_loaded += len(df)
            
            # Atualiza o log com SUCESSO
            finished_at = datetime.now(timezone.utc).isoformat()
            con.execute(
                """
                UPDATE etl_load_log 
                SET status = 'SUCCESS', finished_at = ?, rows_loaded = ? 
                WHERE load_id = ?
                """,
                (finished_at, total_loaded, load_id)
            )
            con.commit()
            print("Pipeline finalizada e tabelas gravadas com sucesso no SQLite.")

        except Exception as e:
            finished_at = datetime.now(timezone.utc).isoformat()
            con.execute(
                """
                UPDATE etl_load_log 
                SET status = 'ERROR', finished_at = ?, error_message = ? 
                WHERE load_id = ?
                """,
                (finished_at, str(e), load_id)
            )
            con.commit()
            raise e


if __name__ == "__main__":
    run_pipeline()