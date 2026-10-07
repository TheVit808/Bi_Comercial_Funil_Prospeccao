import sqlite3
from datetime import datetime

with sqlite3.connect("data/bi_comercial.db") as con:
    con.execute(
        "INSERT INTO etl_load_log (pipeline_name, status, loaded_at) VALUES (?, ?, ?)",
        ("pipeline_comercial", "SUCCESS", datetime.now().isoformat())
    )
    con.commit()