# Private Credit Performance – Tech Assessment

A reproducible Python workflow for ingesting, cleaning, and analyzing private credit cash flow data.  
The goal is to normalize raw CSV inputs, compute XIRR/MOIC metrics, model leverage impact, and output a clean summary table.

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/zhouyichen30/pc_project.git
cd pc_project
```

### 2. Create and activate a virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux
source venv/bin/activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install pandas pathlib
pip freeze > requirements.txt
```

---

## ✅ Progress Summary

### 📍 Current Status
**Goal:** Build an end-to-end pipeline for private credit data analysis as part of a technical assessment.

**What’s Completed So Far:**

#### 🧩 Environment & Git Setup
- Initialized local Git repository and pushed to GitHub (`pc_project`).
- Structured directories into modular components:
  ```
  data/
  src/
    ├── clean.py
    └── utils.py
  ```
- Set up virtual environment and dependency management.
- Verified `.gitignore` excludes `venv/` and nonessential local files.

#### 🧼 Data Cleaning
- Implemented `clean_data()` in `src/utils.py`:
  - Converts date columns → `datetime` (`errors='coerce'`)
  - Strips and lowercases text columns (`.str.strip().str.lower()`)
  - Converts numeric columns → `float` (`pd.to_numeric(errors='coerce')`)
  - Includes validation (`if col in df.columns`) and `.copy()` safety.
- Verified output dtypes and confirmed clean DataFrame structure.

#### 📜 Script Integration
- `src/clean.py` reads `data/cashflows_deal.csv` via `Path` and calls `clean_data()`.
- Prints data type summary and head of cleaned dataset for verification.

#### 🧭 Git Workflow
- Confirmed `git add`, `git commit`, and `git push` functionality.
- Verified synchronization between local and remote repository.

---

## 🧭 Next Steps

**Data & Metrics**
- Enforce sign conventions:
  - Contributions = negative cash flows
  - Distributions/returns = positive cash flows
- Merge with `structure.csv` to link facilities → deals → funds.
- Implement and validate Excel-style **XIRR** calculation.
- Compute facility/deal/fund-level:
  - Paid-in capital  
  - Distributions  
  - Gross & net IRR / MOIC  

**Leverage Modeling**
- Use `leverage.csv` + `curves.csv` to estimate financing cost.
- Model gross vs. net performance and produce fund-level results.

**Outputs**
- Export single summary file `performance_summary.csv` with:
  ```
  level,id,name,paid_in,distributed,gross_irr,gross_moic,net_irr,net_moic
  ```

**Stretch Goals**
- Rate shock (+100 bps parallel shift)
- PIK / delayed-draw modeling using `terms.csv`

---

## ▶️ How to Run the Current Version

### Clean the dataset
Key Behaviors

Date columns:
Converted using pd.to_datetime(errors='coerce') — invalid strings become NaT.

Text columns:

Leading/trailing whitespace removed

Converted to lowercase

Multiple spaces or underscores replaced with a single underscore ("exit fee" → "exit_fee")

Numeric columns:
Converted to float using pd.to_numeric(errors='coerce'), coercing invalid strings to NaN.

Malformed rows:
For this script I only treat date as malformed role as for example, fixed coupon rate term loan's spread will show na

finds:
The log finds that in curve data there are sofr and s0dr and euribor and eurib0r so we need to addtional clean these data

curve
sofr       23
euribor    23
eurib0r     1
s0fr        1

strcture data is pretty clean by looking at the cleanning logs. The only finds after clean is that region has some na values
nan    4
eu     1
but since region data will not be used in this project so we will not further clean it. In case we need it in the future, we will add another script called clean_stecture data or we need to contact data vendor to provide better quality of data.

# curve data addiononal clean
this script is called clean_curve_.py which it clean sepefic clean euribor and data

# merging
a merge.py script contains all the merging code

The first step merge starts integrates multiple financial datasets into a unified analytical table. Cleaned data from cashflow_df_cleaned, term_df, structure_df, and leverage_df are merged using key relationships between entities. Specifically, cashflow_df_cleaned.entity_id is joined with term_df.facility_id and structure_df.facility_id to align transactional cashflows with facility and deal-level attributes. The resulting dataset is then linked to leverage_df on the fund field

I used outer join for my merger because its easier to debug if we have addtional role that is not cleaned which it will show na

quality check - merger data is most important in this project in my opinion, thus build two quality data checks in the logg which check if the meregd data contain na or duplcaited data.

The second step is merging the curve data. For this excersied I merged the curve data on the fund level cost_of_funds_curve since we assume the intrest rate is fixed. If I have more time, I would merge on the deal level so we can model the deal level curve




# Logging:
Uses the shared project logger (pc_project) to record:

Input/output shape

Cleaning steps completed

Top 5 value distributions for each text column so when i build this code I know every dataset to clean first before I join them togther

for cash_flow_sign_convert funcation, it will log the sign coverted status, for _clean_entity_id it log if o is converet to 0q

for mergedb it loggs the shape after every merge

## 🧠 References

### Data Cleaning Function
```python
from utils import clean_data
cash_flow = clean_data(cash_flow, date_cols, text_cols, num_cols)
```

### Git Workflow
```bash
git status
git add .
git commit -m "Add clean_data function and setup"
git push origin main
```

---

**Author:** [Yichen Zhou](https://github.com/zhouyichen30)  

##Logging Setup

The project uses Python’s built-in logging module to track all processing steps, warnings, and errors across scripts.
A single centralized logger is configured in src/utils.py, and all functions (e.g., clean_data(), merge_structure(), etc.) write to it.

How It Works

When you run any script (e.g. python -m src.clean), the logger automatically:

Writes logs to both the console and a file located in:

logs/project.log

I have one script to handle each csv's cleanning and golbal cleaning funcation are stored in utils
## process

this script will read all the csv to clean the data. A centerliazed clean data funcation is written in the utils.py which it will clean date, string, and number type of data columns. And it will log the unique values for all the text columns so that when I doing this project I know if there are some data issue by reading the log.

If the log finds data issue, then I create one clean script for any sepefic data issue that related to that database csv.

One finds is that structure_df.fund is like hbc_private_credit_fund_i but leverage_df fund is like HBC Private Credit Fund I so before merge is data we need to make sure this two data is cleaned. hbc_private_credit_fund_i formate is better than HBC Private Credit Fund I  thus we need to convert fund data formate for leverage_df.fund column

cashflow_deal.csv has its own clean_cash_flow.py that first convert replace o to 0 in the enity id column
and it convert all the sign convecation

Please note that covenants data is not used in this project

Then merge starts integrates multiple financial datasets into a unified analytical table. Cleaned data from cashflow_df_cleaned, term_df, structure_df, and leverage_df are merged using key relationships between entities. Specifically, cashflow_df_cleaned.entity_id is joined with term_df.facility_id and structure_df.facility_id to align transactional cashflows with facility and deal-level attributes. The resulting dataset is then linked to leverage_df on the fund field

I used outer join for my merge 

## model Assumtions
No additional base currency conversation is needed; we can report IRR/MOIC in the fund’s currency as defined in the structure.csv.

I assume the reset rate for this model is monthly based. Each cashflow uses the most recent curve on or before the cashflow date for fund level fiancing cost calculation For this exercise, the base-rate curves (e.g., SOFR, EURIBOR) were merged at the fund level using the cost_of_funds_curve field.
This approach assumes that all facilities within a fund share the same cost of financing, consistent with the instruction that the provided cash flows are fixed and not meant to be recalculated at a deal level.

In a production environment or with more time, I would enhance this by merging the curves at the deal or facility level, allowing each exposure to follow its specific reference curve and tenor. That would enable a more granular and realistic modeling of floating-rate cash flows and sensitivity analysis.

both OID and origination fees wil be treated as day-one adjustments. Added a function to adjust that
treat the provided cash flows as fixed for this exercise; the curves are intended for optional rate-sensitivity analysis.


## future imporvment

1. qulaity contorl for currency data for example, make sure all entity type euro has euro

2. base and local irr, I would like to get the fx rate to convert these cashflow from local to base as USD