# BI Comercial — Funil de Prospecção

Projeto de portfólio para construir uma base analítica de **leads, interações, oportunidades e receita**, com ETL em Python, modelo dimensional em SQLite e artefatos CSV/Parquet para consumo analítico ou Power BI.

## Arquitetura

```text
CRM / Excel / API simulada
          ↓
     data/raw/
          ↓
 data/sample (CSV/Parquet)
          ↓
 src/etl/pipeline.py
          ↓
 data/bi_comercial.db (SQLite)
          ↓
 reconciliações e testes
```

O modelo é composto por:

- **Dimensões:** `dim_date`, `dim_lead`, `dim_sales_rep`, `dim_channel`;
- **Fatos:** `fact_interaction`, `fact_opportunity`, `fact_revenue`;
- **Controle:** `etl_load_log` e `etl_rejection_log` no esquema SQL.

As principais regras de negócio são: `SQL ⊆ MQL`, oportunidades somente para leads SQL, receita somente para oportunidades ganhas e valores não ganhos iguais a zero. Anomalias devem ser identificadas por `anomaly_flag` e não removidas silenciosamente.

## Dados de amostra

Os arquivos em `data/sample/` estão disponíveis em CSV e Parquet. O snapshot atual contém aproximadamente:

| Entidade | Registros |
|---|---:|
| Leads | 30.000 |
| Interações | 86.139 |
| Oportunidades | 2.351 |
| Receita | 1.138 |
| Vendedores | 24 |
| Datas | 731 |

`data/sample/validation.json` registra as evidências de qualidade e reconciliação, incluindo 5.700 leads SQL, R$ 88.363.334,87 de receita e ausência de chaves órfãs no snapshot.

## Execução local

Requisitos: Python 3.11+ e os pacotes listados em `requirements.txt`.

```bash
python3 -m pip install -r requirements.txt
python3 src/etl/pipeline.py
python3 -m pytest tests/ -v
```

No Windows, o script `run.ps1` oferece atalhos:

```powershell
.\run.ps1 setup
.\run.ps1 run
.\run.ps1 test
.\run.ps1 reconcile
```

O pipeline lê Parquet de `data/sample/`, cria/atualiza `data/bi_comercial.db`, carrega as tabelas principais e registra o resultado em `etl_load_log`. A reconciliação SQL usa `sql/02_reconciliation.sql`.

## Geração e organização

- `src/etl/generate_dataset.py`: geração determinística de dados sintéticos, com semente `42` e período de 2024-01-01 a 2025-12-31;
- `src/etl/`: extração, transformação, carga, validação e pipeline;
- `database/bi_comercial.sql`: esquema SQLite completo, staging, dimensões, fatos e logs;
- `sql/`: scripts de schema, cargas e reconciliação;
- `tests/`: testes de qualidade do funil e da carga;
- `docs/guia-trilha-a.md`: especificação detalhada da Trilha A.

> **Estado atual:** os Parquets completos em `data/sample/` são o snapshot de referência. O gerador atualmente recria apenas `dim_lead`, e alguns módulos auxiliares (`extract.py`, `transform.py`, `load.py`) e scripts SQL permanecem como scaffolding; a implementação executável principal está em `src/etl/pipeline.py`.
