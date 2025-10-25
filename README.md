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




Logging:
Uses the shared project logger (pc_project) to record:

Input/output shape

Cleaning steps completed

Top 5 value distributions for each text column

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

## Assumtions
# No additional base currency conversation is needed; we can report IRR/MOIC in the fund’s currency as defined in the structure.csv.

# both OID and origination fees wil be treated as day-one adjustments. Added a function to adjust that
# treat the provided cash flows as fixed for this exercise; the curves are intended for optional rate-sensitivity analysis.
