
# Dicionário de Métricas

## Leads

- Definição: quantidade distinta de leads criados no contexto filtrado.
- Numerador: quantidade distinta de `dim_lead[lead_key]`.
- Denominador: não se aplica.
- Granularidade: lead.
- Data padrão: `dim_lead[created_date]`.
- Fonte: `dim_lead`.
- Limitações: registros sintéticos.

## Conversão MQL

- Definição: MQLs divididos pelo total de leads.
- Numerador: leads com `mql_flag = TRUE`.
- Denominador: total de leads.
- Granularidade: lead.
- Data padrão: `created_date`.
- Fonte: `dim_lead`.
- Limitações: a data de entrada é usada como referência da coorte.
