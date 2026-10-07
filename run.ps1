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
        Write-Host "Executando a pipeline de ETL antes da reconciliacao..." -ForegroundColor Cyan
        python src/etl/pipeline.py
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falha na execucao da pipeline ETL. Reconciliacao abortada."
            exit $LASTEXITCODE
        }

        Write-Host "Executando reconciliacao SQL..." -ForegroundColor Cyan
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