import pandas as pd
from pathlib import Path
from utils import clean_data   # import the helper function


# Get the project root (one level up from src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the data folder path
data_path = BASE_DIR / "data"
# Read the CSV
cash_flow = pd.read_csv(data_path/ "cashflows_deal.csv")
#clean date columns
cash_flow_date_cols = ['asof']
cash_flow_text_cols = ['entity_id','entity_type','cashflow_type','currency']
cash_flow_num_cols = ['amount']

# ---- CLEANING ----


df = clean_data(cash_flow,cash_flow_date_cols,cash_flow_text_cols,cash_flow_num_cols)
print(df.dtypes)
