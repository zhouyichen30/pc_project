import pandas as pd
from pathlib import Path
import numpy as np
from utils import clean_data_format   # import the helper function
from clean_cash_flow import cash_flow_sign_convert


# Get the project root (one level up from src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the data folder path
data_path = BASE_DIR / "data"
OUT_path = BASE_DIR / "outputs"

# Read the CSV
cash_flow = pd.read_csv(data_path/ "cashflows_deal.csv")
term_df = pd.read_csv(data_path/ "terms.csv")
#clean date columns
cash_flow_date_cols = ['asof']
cash_flow_text_cols = ['entity_id','entity_type','cashflow_type','currency']
cash_flow_num_cols = ['amount']

term_data_date_cols = []
term_data_text_cols = ['facility_id','rate_type','day_count','pik','delayed_draw']
term_data_num_cols = ['spread_bps','origination_fee_bps','OID_bps','amort_pct_per_qtr','fixed_rate_bps']

# ---- CLEANING ----
cashflow_df = clean_data_format(cash_flow,cash_flow_date_cols,cash_flow_text_cols,cash_flow_num_cols)
term_df = clean_data_format(term_df,term_data_date_cols,term_data_text_cols,term_data_num_cols)

cashflow = cash_flow_sign_convert(cashflow_df)
print(term_df)