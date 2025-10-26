import pandas as pd
from pathlib import Path
import numpy as np
from utils import clean_data_format   # import the helper function
from clean_cash_flow import cash_flow_clean
from clean_curve import clean_curve_df
from merge import merge_db,merge_curve
from cash_flow_adjust import adjust_cash_flow
from metrics import metrics
from level_merge import merge_deal_level

# Get the project root (one level up from src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the data folder path
data_path = BASE_DIR / "data"
OUT_path = BASE_DIR / "outputs"

# Read the CSV
cash_flow = pd.read_csv(data_path/ "cashflows_deal.csv")
term_df = pd.read_csv(data_path/ "terms.csv")
curve_df = pd.read_csv(data_path/ "curves.csv")
structure_df = pd.read_csv(data_path/ "structure.csv")
leverage_df = pd.read_csv(data_path/ "leverage.csv")

#clean date, text, and number columns for all dataframe for this project
cash_flow_date_cols = ['asof']
cash_flow_text_cols = ['entity_id','entity_type','cashflow_type','currency']
cash_flow_num_cols = ['amount']

term_data_date_cols = []
term_data_text_cols = ['facility_id','rate_type','day_count','pik','delayed_draw']
term_data_num_cols = ['spread_bps','origination_fee_bps','OID_bps','amort_pct_per_qtr','fixed_rate_bps']

curve_data_date_cols = ['asof']
curve_data_text_cols = ['curve']
curve_data_num_cols = ['rate']

structure_data_date_cols=[]
structure_data_text_cols=['facility_id','facility_name','deal_id','deal_name','strategy_bucket','region','sector','fund']
structure_data_num_cols = []

leverage__data_date_cols=[]
leverage__data_text_cols=['fund','cost_of_funds_curve']
leverage_data_num_cols = ['advance_rate','spread_bps','undrawn_fee_bps','commitment']
#asof,curve,rate

# ---- CLEANING ----
cashflow_df = clean_data_format(cash_flow,cash_flow_date_cols,cash_flow_text_cols,cash_flow_num_cols)
#further clean cashflow data
cashflow_df_cleaned = cash_flow_clean(cashflow_df)

term_df_cleaned = clean_data_format(term_df,term_data_date_cols,term_data_text_cols,term_data_num_cols)

curve_df = clean_data_format(curve_df,curve_data_date_cols,curve_data_text_cols,curve_data_num_cols)
#futher clean curve data
curve_df_cleaned = clean_curve_df(curve_df)

structure_df_cleaned = clean_data_format(structure_df,structure_data_date_cols,structure_data_text_cols,structure_data_num_cols)


leverage_df_cleaned = clean_data_format(leverage_df,leverage__data_date_cols,leverage__data_text_cols,leverage_data_num_cols)
#merge the term data, cashflow data, structure data and leverage data together
mdb = merge_db(cashflow_df_cleaned,term_df_cleaned,structure_df_cleaned,leverage_df_cleaned)
# Merge curves at the fund level using cost_of_funds_curve.
# Assumption: For this assessment, interest rates are treated as fixed.
# In a full implementation, we would merge at the deal/facility level
# to capture distinct base-rate exposures (e.g., SOFR vs. EURIBOR).
mdbc = merge_curve(mdb, curve_df_cleaned)

mdc_cleanned = adjust_cash_flow(mdbc)

#write the cleanned data to a csv files
mdc_cleanned.to_csv(OUT_path / 'cleanned_cashflow_master_3.csv')

#now calcaulte the metrics
#calculate for each levels
#please make sure the lower level is the first entry in the list for irr calc purpose
level_3 = ['entity_id','deal_id','fund']
level_3_metrics_db = metrics(level_3,mdc_cleanned)

#level 2 is on deal level
level_2 = ['deal_id','fund']
level_2_metrics_db = metrics(level_2,mdc_cleanned)

#level 1 is on fund level
level_1 = ['fund']
level_1_metrics_db = metrics(level_1,mdc_cleanned)


#merge all levels
mldb = merge_deal_level(level_3_metrics_db,level_2_metrics_db,level_1_metrics_db)
#write mdb as csv
mldb.to_csv(OUT_path / 'cleanned_net_irr_all_levels.csv')