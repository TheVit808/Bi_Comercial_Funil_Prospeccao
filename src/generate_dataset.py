from __future__ import annotations

from pathlib import Path
import json
import sqlite3

import numpy as np
import pandas as pd

SEED = 20261005
N_LEADS = 30_000
START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")
OUT = Path(__file__).resolve().parents[1] / "data" / "sample"
RNG = np.random.default_rng(SEED)


def weighted_choice(values, probs, n):
    return RNG.choice(values, size=n, p=np.asarray(probs) / np.sum(probs))


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def daterange_dates(start, end):
    return pd.date_range(start, end, freq="D")


def build_dimensions():
    dates = daterange_dates(START, END)
    dim_date = pd.DataFrame({"date_key": dates.strftime("%Y%m%d").astype(int), "date": dates})
    dim_date["year"] = dates.year
    dim_date["quarter"] = "Q" + dates.quarter.astype(str)
    dim_date["month"] = dates.month
    dim_date["month_name"] = dates.month_name(locale="pt_BR.UTF-8") if False else dates.strftime("%B")
    dim_date["week_of_year"] = dates.isocalendar().week.astype(int)
    dim_date["day_of_week"] = dates.dayofweek + 1
    dim_date["is_weekend"] = dates.dayofweek >= 5
    dim_date["month_start"] = dates.to_period("M").to_timestamp()

    channels = [
        (1, "Inbound - Site", "Digital", 0.20, 0.18, 0.70),
        (2, "Outbound - SDR", "Prospecção ativa", 0.18, 0.24, 0.56),
        (3, "Indicação", "Parcerias", 0.13, 0.34, 0.82),
        (4, "Evento", "Marketing", 0.10, 0.28, 0.65),
        (5, "Mídia paga", "Digital", 0.25, 0.16, 0.48),
        (6, "Marketplace/API", "Integração", 0.14, 0.21, 0.58),
    ]
    dim_channel = pd.DataFrame(channels, columns=["channel_key", "channel_name", "channel_group", "share", "base_conversion", "base_quality"])

    reps = []
    names = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fabio", "Gabriela", "Henrique", "Isabela", "João", "Karen", "Lucas", "Marina", "Nicolas", "Olivia", "Paulo", "Rafaela", "Sergio", "Tatiana", "Ulysses", "Valeria", "William", "Yasmin", "Zeca"]
    regions = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
    for i, name in enumerate(names, 1):
        reps.append((i, f"{name} {chr(64 + ((i * 3) % 26 or 26))}", regions[(i - 1) % len(regions)], "Pleno" if i % 3 else "Sênior", START + pd.Timedelta(days=int(RNG.integers(0, 180)))))
    dim_sales_rep = pd.DataFrame(reps, columns=["sales_rep_key", "sales_rep_name", "region", "seniority", "hire_date"])
    return dim_date, dim_channel, dim_sales_rep


def generate_leads(dim_channel, dim_sales_rep):
    channel_keys = dim_channel.channel_key.to_numpy()
    channel_probs = dim_channel.share.to_numpy()
    lead_dates = pd.date_range(START, END, freq="D")
    # Mais entradas no início do ano e em meses de campanha, menos em janeiro/dezembro.
    season = np.array([1.05, 1.00, 1.08, 1.12, 1.16, 1.10, 0.98, 1.03, 1.12, 1.18, 1.15, 0.72])
    day_weights = np.array([season[d.month - 1] * (0.72 if d.dayofweek >= 5 else 1.0) for d in lead_dates])
    day_weights /= day_weights.sum()
    dates = pd.to_datetime(RNG.choice(lead_dates.values, size=N_LEADS, p=day_weights)).normalize()
    channel = weighted_choice(channel_keys, channel_probs, N_LEADS)
    region = weighted_choice(dim_sales_rep.region.unique(), [0.43, 0.19, 0.18, 0.12, 0.08], N_LEADS)
    segment = weighted_choice(["PME", "Mid-market", "Enterprise"], [0.56, 0.32, 0.12], N_LEADS)
    company_size = np.where(segment == "PME", RNG.integers(5, 80, N_LEADS), np.where(segment == "Mid-market", RNG.integers(80, 500, N_LEADS), RNG.integers(500, 8000, N_LEADS)))
    rep_by_region = {r: dim_sales_rep.loc[dim_sales_rep.region == r, "sales_rep_key"].to_numpy() for r in dim_sales_rep.region.unique()}
    rep = np.array([RNG.choice(rep_by_region[r]) for r in region])
    source_system = weighted_choice(["CRM", "Excel", "API simulada"], [0.62, 0.23, 0.15], N_LEADS)
    channel_quality = dim_channel.set_index("channel_key").base_quality.reindex(channel).to_numpy()
    segment_effect = np.select([segment == "Enterprise", segment == "Mid-market"], [0.35, 0.12], 0)
    weekday_effect = np.where(pd.Series(dates).dt.dayofweek.to_numpy() < 5, 0.10, -0.12)
    noise = RNG.normal(0, 0.95, N_LEADS)
    lead_score = np.clip(52 + 18 * (channel_quality - 0.55) + 10 * segment_effect + 4 * weekday_effect + noise * 7, 1, 99).round().astype(int)
    status_prob = sigmoid((lead_score - 53) / 10)
    mql = RNG.random(N_LEADS) < status_prob * 0.72
    sql = mql & (RNG.random(N_LEADS) < (0.28 + 0.004 * lead_score))
    lead_id = np.arange(1, N_LEADS + 1)
    dim_lead = pd.DataFrame({
        "lead_key": lead_id,
        "lead_id_business": [f"LD-{d.strftime('%Y%m%d')}-{i:05d}" for i, d in zip(lead_id, dates)],
        "created_date": dates,
        "created_date_key": pd.to_datetime(dates).strftime("%Y%m%d").astype(int),
        "channel_key": channel,
        "sales_rep_key": rep,
        "region": region,
        "segment": segment,
        "company_size_employees": company_size,
        "lead_score": lead_score,
        "is_mql": mql,
        "is_sql": sql,
        "source_system": source_system,
        "is_test_record": False,
    })
    # Outliers controlados: 1% de scores muito altos, preservando rastreabilidade.
    anomaly_idx = RNG.choice(dim_lead.index, size=int(N_LEADS * 0.01), replace=False)
    dim_lead.loc[anomaly_idx, "lead_score"] = RNG.choice([98, 99], size=len(anomaly_idx))
    dim_lead["anomaly_flag"] = False
    dim_lead.loc[anomaly_idx, "anomaly_flag"] = True
    return dim_lead


def generate_interactions(dim_lead):
    rows = []
    interaction_id = 1
    types = ["Ligação", "E-mail", "WhatsApp", "Reunião", "Demonstração"]
    outcomes = ["Sem resposta", "Conectado", "Qualificado", "Follow-up", "Desqualificado"]
    for r in dim_lead.itertuples(index=False):
        n = int(np.clip(RNG.poisson(2.8 if r.is_mql else 1.3) + 1, 1, 10))
        for seq in range(n):
            delta_days = int(RNG.gamma(2.2, 3.5)) + seq * 2
            interaction_date = r.created_date + pd.Timedelta(days=delta_days)
            if interaction_date > END:
                interaction_date = END
            typ = weighted_choice(types, [0.31, 0.28, 0.16, 0.16, 0.09], 1)[0]
            if r.is_sql and seq == n - 1:
                outcome = "Qualificado"
            else:
                outcome = weighted_choice(outcomes, [0.32, 0.30, 0.13, 0.19, 0.06], 1)[0]
            response = float(np.clip(RNG.lognormal(np.log(18 if typ == "E-mail" else 7), 0.65), 0.2, 240))
            rows.append((interaction_id, r.lead_key, r.sales_rep_key, r.channel_key, interaction_date, typ, outcome, round(response, 2), r.source_system))
            interaction_id += 1
    fact = pd.DataFrame(rows, columns=["interaction_key", "lead_key", "sales_rep_key", "channel_key", "interaction_date", "interaction_type", "outcome", "response_time_hours", "source_system"])
    outlier_n = max(1, int(len(fact) * 0.012))
    outlier_idx = RNG.choice(fact.index, size=outlier_n, replace=False)
    fact.loc[outlier_idx, "response_time_hours"] = RNG.uniform(240, 720, outlier_n).round(2)
    fact["anomaly_flag"] = False
    fact.loc[outlier_idx, "anomaly_flag"] = True
    fact["interaction_date_key"] = fact.interaction_date.dt.strftime("%Y%m%d").astype(int)
    return fact


def generate_opportunities(dim_lead):
    eligible = dim_lead[dim_lead.is_sql].copy()
    if eligible.empty:
        return pd.DataFrame()
    conv_by_segment = {"PME": 0.34, "Mid-market": 0.42, "Enterprise": 0.51}
    conv_by_channel = {1: 1.05, 2: 0.90, 3: 1.28, 4: 1.08, 5: 0.80, 6: 0.96}
    p_opp = np.array([conv_by_segment[s] * conv_by_channel[c] for s, c in zip(eligible.segment, eligible.channel_key)])
    p_opp = np.clip(p_opp * (0.75 + eligible.lead_score.to_numpy() / 180), 0.08, 0.88)
    is_opp = RNG.random(len(eligible)) < p_opp
    opp = eligible[is_opp].copy().reset_index(drop=True)
    n = len(opp)
    if n == 0:
        return pd.DataFrame()
    opp_key = np.arange(1, n + 1)
    created = opp.created_date + pd.to_timedelta(RNG.integers(2, 35, n), unit="D")
    stage_prob = np.clip(0.42 + (opp.lead_score.to_numpy() - 50) / 180, 0.18, 0.78)
    won = RNG.random(n) < stage_prob
    open_ = (~won) & (RNG.random(n) < 0.28)
    status = np.where(won, "Won", np.where(open_, "Open", "Lost"))
    close_days = RNG.integers(10, 90, n)
    close_date = created + pd.to_timedelta(close_days, unit="D")
    close_date = pd.Series(close_date).where(status != "Open", pd.NaT)
    base_value = np.where(opp.segment == "PME", RNG.lognormal(np.log(18000), 0.55, n), np.where(opp.segment == "Mid-market", RNG.lognormal(np.log(65000), 0.52, n), RNG.lognormal(np.log(220000), 0.60, n)))
    base_value *= np.where(opp.channel_key == 3, 1.10, 1.0)
    estimated = np.round(base_value / 100) * 100
    discount = np.clip(RNG.normal(0.08, 0.045, n), 0, 0.30)
    final = np.where(won, estimated * (1 - discount), 0)
    fact_opp = pd.DataFrame({
        "opportunity_key": opp_key,
        "opportunity_id_business": [f"OP-{x:06d}" for x in opp_key],
        "lead_key": opp.lead_key,
        "sales_rep_key": opp.sales_rep_key,
        "channel_key": opp.channel_key,
        "created_date": created,
        "created_date_key": created.dt.strftime("%Y%m%d").astype(int),
        "close_date": close_date,
        "close_date_key": pd.to_datetime(close_date).dt.strftime("%Y%m%d").astype("Int64"),
        "status": status,
        "estimated_value_brl": estimated.round(2),
        "discount_pct": discount.round(4),
        "won_value_brl": np.round(final, 2),
        "sales_cycle_days": np.where(status == "Open", (END - created).dt.days, (pd.to_datetime(close_date) - created).dt.days),
        "source_system": "CRM",
    })
    fact_opp["anomaly_flag"] = False
    # 0,8% de ciclos longos, úteis para análise de exceções.
    if n > 100:
        ix = RNG.choice(fact_opp.index, size=max(1, int(n * 0.008)), replace=False)
        fact_opp.loc[ix, "sales_cycle_days"] = RNG.integers(180, 365, len(ix))
        fact_opp.loc[ix, "anomaly_flag"] = True
    return fact_opp


def generate_revenue(fact_opp):
    won = fact_opp[fact_opp.status == "Won"].copy().reset_index(drop=True)
    if won.empty:
        return pd.DataFrame()
    revenue = pd.DataFrame({
        "revenue_key": np.arange(1, len(won) + 1),
        "opportunity_key": won.opportunity_key,
        "lead_key": won.lead_key,
        "sales_rep_key": won.sales_rep_key,
        "channel_key": won.channel_key,
        "revenue_date": won.close_date,
        "revenue_date_key": won.close_date_key,
        "revenue_type": "New business",
        "amount_brl": won.won_value_brl,
        "is_recurring": True,
        "source_system": "ERP simulada",
    })
    revenue["anomaly_flag"] = False
    if len(revenue) > 100:
        ix = RNG.choice(revenue.index, size=max(1, int(len(revenue) * 0.006)), replace=False)
        revenue.loc[ix, "amount_brl"] *= RNG.uniform(2.5, 5.0, len(ix))
        revenue.loc[ix, "amount_brl"] = revenue.loc[ix, "amount_brl"].round(2)
        revenue.loc[ix, "anomaly_flag"] = True
    return revenue


def export(df, name):
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    df.to_parquet(OUT / f"{name}.parquet", index=False, compression="snappy")


def validate(dim_date, dim_lead, dim_channel, dim_sales_rep, fact_interaction, fact_opp, fact_revenue):
    checks = {
        "date_future": int((dim_lead.created_date > END).sum()),
        "duplicate_lead_business_key": int(dim_lead.lead_id_business.duplicated().sum()),
        "orphan_interaction_leads": int((~fact_interaction.lead_key.isin(dim_lead.lead_key)).sum()),
        "orphan_opportunity_leads": int((~fact_opp.lead_key.isin(dim_lead.lead_key)).sum()),
        "orphan_revenue_opportunities": int((~fact_revenue.opportunity_key.isin(fact_opp.opportunity_key)).sum()),
        "funnel_leads": int(len(dim_lead)),
        "funnel_mql": int(dim_lead.is_mql.sum()),
        "funnel_sql": int(dim_lead.is_sql.sum()),
        "opportunities": int(len(fact_opp)),
        "won_opportunities": int((fact_opp.status == "Won").sum()),
        "revenue_total_brl": round(float(fact_revenue.amount_brl.sum()), 2),
        "anomaly_rate_leads": round(float(dim_lead.anomaly_flag.mean()), 4),
        "anomaly_rate_interactions": round(float(fact_interaction.anomaly_flag.mean()), 4),
        "anomaly_rate_opportunities": round(float(fact_opp.anomaly_flag.mean()), 4),
        "anomaly_rate_revenue": round(float(fact_revenue.anomaly_flag.mean()), 4),
    }
    # Reconciliações essenciais do modelo e do funil.
    checks["funnel_mql_not_above_leads"] = bool(checks["funnel_mql"] <= checks["funnel_leads"])
    checks["funnel_sql_not_above_mql"] = bool(checks["funnel_sql"] <= checks["funnel_mql"])
    clean_revenue = fact_revenue.loc[~fact_revenue.anomaly_flag]
    clean_won = fact_opp.loc[(fact_opp.status == "Won") & fact_opp.opportunity_key.isin(clean_revenue.opportunity_key)]
    checks["clean_revenue_reconciles_to_won"] = bool(np.isclose(clean_revenue.amount_brl.sum(), clean_won.won_value_brl.sum(), rtol=0, atol=0.01))
    checks["revenue_outlier_amount_brl"] = round(float(fact_revenue.loc[fact_revenue.anomaly_flag, "amount_brl"].sum()), 2)
    return checks


def main():
    dim_date, dim_channel, dim_sales_rep = build_dimensions()
    dim_lead = generate_leads(dim_channel, dim_sales_rep)
    fact_interaction = generate_interactions(dim_lead)
    fact_opp = generate_opportunities(dim_lead)
    fact_revenue = generate_revenue(fact_opp)
    tables = {"dim_date": dim_date, "dim_lead": dim_lead, "dim_channel": dim_channel, "dim_sales_rep": dim_sales_rep, "fact_interaction": fact_interaction, "fact_opportunity": fact_opp, "fact_revenue": fact_revenue}
    for name, df in tables.items():
        export(df, name)
    checks = validate(dim_date, dim_lead, dim_channel, dim_sales_rep, fact_interaction, fact_opp, fact_revenue)
    (OUT / "validation.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"output_dir": str(OUT), "tables": {k: len(v) for k, v in tables.items()}, "validation": checks}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
