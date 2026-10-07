param (
    [string]$Task = "help"
)

switch ($Task) {
    "setup" {
        python -m pip install -r requirements.txt
    }
    "run" {
        python src/etl/pipeline.py
    }
    "test" {
        python -m pytest -q
    }
    "reconcile" {
        Get-Content sql/02_reconciliation.sql -Encoding UTF8 | sqlite3 data/bi_comercial.db
    }
    Default {
        Write-Host "Comandos disponíveis:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 setup      - Instala as dependências"
        Write-Host "  .\run.ps1 run        - Executa a pipeline ETL"
        Write-Host "  .\run.ps1 test       - Executa os testes unitários"
        Write-Host "  .\run.ps1 reconcile  - Executa a reconciliação no SQLite"
    }
}