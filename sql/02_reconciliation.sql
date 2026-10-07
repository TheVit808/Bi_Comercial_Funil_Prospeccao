-- 1. Contagem de leads na origem e destino
SELECT 'dim_lead' AS table_name, COUNT(*) AS rows_loaded
FROM dim_lead;

-- 2. Duplicidade de chave de negócio
SELECT lead_business_id, COUNT(*) AS occurrences
FROM dim_lead
GROUP BY lead_business_id
HAVING COUNT(*) > 1;

-- 3. Leads sem dimensão relacionada
SELECT COUNT(*) AS orphan_leads
FROM dim_lead l
LEFT JOIN dim_channel c ON c.channel_key = l.channel_key
LEFT JOIN dim_sales_rep r ON r.sales_rep_key = l.sales_rep_key
WHERE c.channel_key IS NULL OR r.sales_rep_key IS NULL;

-- 4. Funil matematicamente monotônico
SELECT
    COUNT(*) AS leads,
    SUM(mql_flag) AS mqls,
    SUM(sql_flag) AS sqls,
    SUM(opportunity_flag) AS opportunities
FROM dim_lead;

-- 5. Receita somente para oportunidades ganhas
SELECT COUNT(*) AS invalid_revenue_rows
FROM fact_revenue r
JOIN fact_opportunity o ON o.opportunity_key = r.opportunity_key
WHERE o.status <> 'Won';

-- 6. Reconciliação de receita líquida
SELECT COUNT(*) AS revenue_formula_errors
FROM fact_revenue
WHERE ABS(net_revenue_brl - (gross_revenue_brl - discount_brl)) > 0.01;

-- 7. Datas futuras fora das anomalias intencionais
SELECT COUNT(*) AS future_clean_interactions
FROM fact_interaction
WHERE interaction_date > '2025-12-31'
  AND anomaly_flag = 0;