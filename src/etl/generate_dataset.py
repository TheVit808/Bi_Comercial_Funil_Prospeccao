from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N_LEADS = 30_000
START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")
RNG = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "sample"
OUT.mkdir(parents=True, exist_ok=True)


def choice(values, probabilities, size):
    return RNG.choice(values, size=size, p=probabilities)


def main():
    dates = pd.date_range(START, END, freq="D")
    lead_id = np.arange(1, N_LEADS + 1)

    created = pd.Series(RNG.choice(dates[:-45], N_LEADS)).sort_values(ignore_index=True)
    segment = choice(["SMB", "Mid-Market", "Enterprise"], [.48, .34, .18], N_LEADS)
    channel = choice(["Inbound", "Paid Media", "Outbound SDR", "Referral"], [.30, .20, .30, .20], N_LEADS)

    quality = np.clip(RNG.normal(.56, .16, N_LEADS), .03, .98)
    mql_probability = np.clip(.16 + .46 * quality, .05, .82)
    mql = RNG.random(N_LEADS) < mql_probability

    sql_probability = np.clip(.10 + .55 * quality, .03, .82)
    sql = mql & (RNG.random(N_LEADS) < sql_probability)

    opportunity_probability = np.clip(.07 + .46 * quality, .02, .75)
    opportunity = sql & (RNG.random(N_LEADS) < opportunity_probability)

    dim_lead = pd.DataFrame({
        "lead_key": lead_id,
        "lead_business_id": [f"LEAD-{x:06d}" for x in lead_id],
        "created_date": created,
        "channel_name": channel,
        "segment": segment,
        "quality_score": quality.round(4),
        "mql_flag": mql,
        "sql_flag": sql,
        "opportunity_flag": opportunity,
    })

    dim_lead.to_csv(OUT / "dim_lead.csv", index=False)
    dim_lead.to_parquet(OUT / "dim_lead.parquet", index=False)
    print(f"Gerados {len(dim_lead):,} leads em {OUT}")

if __name__ == "__main__":
    main()