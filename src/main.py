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
#clean date columns
cash_flow_date_cols = ['asof']
cash_flow_text_cols = ['entity_id','entity_type','cashflow_type','currency']
cash_flow_num_cols = ['amount']

# ---- CLEANING ----
df = clean_data_format(cash_flow,cash_flow_date_cols,cash_flow_text_cols,cash_flow_num_cols)

cashflow = cash_flow_sign_convert(df)
print(cashflow)