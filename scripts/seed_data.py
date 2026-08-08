import os
from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Project & Dataset configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "investment-treasury-ai")  # Replace with your GCP project ID
DATASET_NAME = "raw_treasury"

client = bigquery.Client(project=PROJECT_ID)

def create_dataset():
    dataset_id = f"{PROJECT_ID}.{DATASET_NAME}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset {DATASET_NAME} created/verified successfully.")

def seed_trade_executions():
    np.random.seed(42)
    n_rows = 1000
    
    start_date = datetime.now() - timedelta(days=30)
    dates = [start_date + timedelta(hours=int(x)) for x in np.random.randint(0, 720, n_rows)]
    
    data = {
        "trade_id": [f"TRD-{10000 + i}" for i in range(n_rows)],
        "asset_class": np.random.choice(["US_TREASURY", "CORPORATE_BOND", "MORTGAGE_BACKED", "EQUITY"], n_rows, p=[0.4, 0.3, 0.2, 0.1]),
        "ticker": np.random.choice(["US10Y", "US02Y", "AAPL", "MSFT", "MBB", "LQD"], n_rows),
        "counterparty_id": np.random.choice(["CP-GOLDMAN", "CP-JPMORGAN", "CP-CITI", "CP-BARCLAYS"], n_rows),
        "notional_amount": np.random.uniform(50000, 5000000, n_rows).round(2),
        "yield_pct": np.random.uniform(0.035, 0.055, n_rows).round(4),
        "execution_timestamp": dates,
        "liquidity_tier": np.random.choice(["TIER_1_HIGH", "TIER_2_MEDIUM", "TIER_3_LOW"], n_rows, p=[0.6, 0.3, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    table_id = f"{PROJECT_ID}.{DATASET_NAME}.raw_trade_executions"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Loaded {n_rows} rows into {table_id}")

if __name__ == "__main__":
    create_dataset()
    seed_trade_executions()
