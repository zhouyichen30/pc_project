# Private Credit Performance Analysis

A reproducible Python workflow/app for ingesting, cleaning, and analyzing private credit cash flow data.  
The goal is to normalize raw CSV inputs, compute metrics such as XIRR/MOIC, model leverage impact (net), and output a unified performance summary and chart.


---
> This project was developed and tested on **Python 3.12.10**.  
> Please use Python 3.11 or later to ensure compatibility.



## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/zhouyichen30/pc_project.git

#if not in the pc_project dir
cd pc_project
```

### 2. If no environment activated, create and activate a virtual environment 
```bash
# Activate
# Windows PowerShell
venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the project
From the project root (pc_project/), navigate into the src directory first:
```bash
# CD into SRC
cd src
#run model
python -m irr_calc
```

### 5. (Optional) Apply an interest rate shock
You can “shock” the base-rate curve by an absolute decimal amount before metrics are computed.

```bash
#example command
python -m irr_calc --shock 0.01
```

| Parameter | Unit    | Example   | Meaning                    |
| --------- | ------- | --------- | -------------------------- |
| `--shock` | decimal | `0.01`    | **+100 bps** upward shock  |
|           |         | `-0.0025` | **–25 bps** downward shock |
---
## Inputs Data
**data/**
- all the CSVs provided are saved into the data folder 
---
## Output

### Main Outputs 

**Outputs/**
- `cleanned_gross_irr_all_level.csv` – gross IRR only, indicate QC output before fund-level aggregation
- `performance_summary.csv` – Final deliverables inculdes net irr/moic on fund level
- `irr_plot.png` – visualization comparing Gross vs. Net IRR breakdown by facility ,deal, and fund


**Outputs/cash_master/**
- `cleanned_cashflow_master.csv` – fully cleaned and merged data prior to modeling
- `cleanned_cashflow_master_fund_added.csv` – cleaned data with fund-level expense added for net IRR


**Outputs/fund_level/**
- `fund_info.csv` – aggregated from raw cashflows
- `fund_curve.csv` – joined with monthly curve rates
- `fee_calc.csv` – monthly interest and undrawn fee cashflows

---

## Modeling Assumptions

### General
- No base-currency conversion
- Provided facility level cashflows are treated as fixed.

### Curves and Financing
- Rates reset monthly.
- Each cashflow uses the most recent curve rate on or before its date.
- Curves merged at fund level (`cost_of_funds_curve`).
- With more time, curves would be merged at deal/facility level for more granular rate modeling.

### Fees and OID
- Both treated as day-one adjustments.
- Implemented via `adjust_fees()` in `cash_flow_adjust.py`.
- Facility F002 (delayed draw) applies both on each contribution.

### PIK Interest
- All PIK interest found accrued and removed.
- In production, a QC step would verify PIK classification before removal.

### Delayed Draw (Facility F002)
- Draw 1: 2023-02-15  
- Draw 2: 2025-05-15  
- Interest currently assumed on total notional.  
- Ideally, interest and PIK would adjust per draw schedule.

### Fund-Level Financing Assumptions
- Drawn Amount — Each capital contribution is treated as a draw on the fund’s credit facility based on advance rate:
  - drawn = contribution_amount × advance_rate
- Credit Line Size — Each fund’s total credit line is set at 20% of total committed capital:
  - credit_line = commitment × 0.20
- Undrawn Balance Logic  
  For the first draw per fund, the undrawn balance is reduced by the amount drawn:
  - undrawn = credit_line + finance_portion  
  (e.g., if credit_line = 80M and first draw = –60.95M → undrawn = 19.05M)

  For subsequent draws or repayments, the undrawn reflects the period’s net movement only:
  - undrawn = finance_portion  
  (e.g., a second draw of –2.96M represents a further use of the credit line.)

- Repayment Timing — The credit line is assumed to be fully repaid once at the fund’s exit_date.
- Cost of Funds Spread (bps) and Undrawn Fee (bps) are modeled as annualized rates.
- Both are accrued monthly, based on the outstanding drawn and undrawn balances at each period.
- These parameters are merged with curve data (SOFR, EURIBOR) to compute:
  - fund-level Interest Expense: drawn × ((curve_rate + spread_bps)/10,000) × days/360
  - Undrawn Fee Expense: undrawn × (undrawn_fee_bps/10,000) × days/360
- Payment date rule: interest/fees paid on the 15th of the following month.
- Month-end expansion window: includes only month-ends ≥ con_date and ≤ exit_date.
- First period anchor: prior month-end of con_date used for rate alignment.
- No working-day adjustment and no floor on rates.

### Rates Shock
- Shocking impact only apply on the fund level
- It only applies parallel shocks to the monthly interest rate data.
- When shocking interest rates, interest cannot become negative.

### IRR
- Paid-in capital treated as negative.
- Distributions treated as positive.
- Fund level expenses reduce distributions.

### Other Simplifications
- No interest-rate floors.
- No currency-level QC or FX normalization.
- `covenants.csv` not used.

---
## Model Workflow
1. **Clean and standardize all input datasets**
   - Read all raw CSVs from `/data/`: `cashflows_deal.csv`, `terms.csv`, `structure.csv`, `leverage.csv`, and `curves.csv`.
   - Normalize date, text, and numeric columns using `clean_data_format()`.
   - Apply specialized cleaners:
     - `cash_flow_clean()` — fixes sign conventions and filters malformed rows.
     - `clean_curve_df()` — fixes curve labels, shock the rates if shock applied

2. **Merge standardized datasets**
   - Merge cleaned cashflow, term, structure, and leverage data with `merge_db()`.
   - Merge fund-level curve data with `merge_curve()` using `cost_of_funds_curve` and prior month-end anchors.
   

3. **Adjust cashflows for fees and PIK**
   - Apply origination, OID, and non-cash PIK adjustments via `adjust_cash_flow()`.
   - Save cleaned and adjusted master dataset.
   - Output intermediate dataset → `/outputs/cash_master/cleanned_cashflow_master.csv`.

4. **Compute multi-level metrics**
   - Use `metrics()` to compute Paid-In, Distributed, MOIC, and IRR at:
     - Facility level (`['entity_id','facility_name','deal_id','fund']`)
     - Deal level (`['deal_id','deal_name','fund']`)
     - Fund level (`['fund']`)
   - Merge metrics across hierarchy levels with `merge_deal_level()`.
   - Output gross-level metrics → `/outputs/cleanned_gross_irr_all_levels.csv`.

5. **Compute fund-level financing and fee accruals**
   - Run `run_fund_level_pipeline()` to calculate interest expense and undrawn fees using monthly curves.
   - Append fee and financing data to master cashflow using `stack_fund_fees_into_master()`.
   - Output → `/outputs/cash_master/cleanned_cashflow_master_fund_added.csv`.

6. **Compute and merge net IRR/MOIC metrics**
   - Recalculate net metrics at fund level using `metrics()`.
   - Merge with gross metrics using `assign_fund_net_metrics()`.
   - Output consolidated summary → `/outputs/performance_summary.csv`.

7. **Visualization and quality control**
   - Generate IRR comparison chart (`plot_irr_highlighted()`) visualizing gross vs. net IRR by hierarchy level.
   - Log all steps and validation info in `logs/project.log`.

---
## Key Function

**How Data Is Cleaned (Pipeline Overview)**
Implemented in `src/irr_calc/clean_cash_flow.py`, `src/irr_calc/clean_curve.py`, and `src/irr_calc/utils.py`.

**Common cleaning steps in (`src/irr_calc/utils.py`):**
- Dates converted using `pd.to_datetime(errors="coerce")`.
- Text normalized with `.str.strip().str.lower()`.
- Numerics coerced using `pd.to_numeric(errors="coerce")`.
- Duplicates removed; top-5 NA summaries logged.
- File-specific cleaners for cashflow, curve, and structure files.

**Cashflow cleaning (`clean_cash_flow.py`):**
- Normalize key columns (`entity_id`, `deal_id`, `fund`, `date`, `amount`, `type`).
- Enforce sign conventions (contributions negative, distributions positive).
- Apply OID/origination adjustments via `adjust_fees()`.
- Remove accrued PIK via `_adjust_pik()`.
- Drop malformed date type rows and log shape/NA counts.

**Curve cleaning (`clean_curve.py`):**
- Normalize columns: `asof`, `curve`, `rate`.
- Fix label typos (`s0fr` → `sofr`, `eurib0r` → `euribor`).
- Clip negative rates after shock.
- Join to master by `(cost_of_funds_curve, month_end_asof)`.

**IRR Calc:**
**`xirr(cashflows, dates)` in src/irr_calc/metrics.py**
Computes the Internal Rate of Return (IRR) for irregularly spaced cashflows using Newton’s method on `_xnpv()`.

**`_xnpv(rate, cashflows, dates)` in src/irr_calc/metrics.py**
Computes the Net Present Value (NPV) for irregularly spaced cashflows, consistent with Excel’s XNPV.

**Formula**
```
NPV(r) = Σ [ CF_i / (1 + r)^((t_i - t_0)/365) ]
```

**Notes**
- Uses ACT/365 day count.
- `t_0` = earliest date in the cashflow series.
- Raises ValueError if input lengths mismatch.

**Purpose**
- Used as f(r) in Newton’s method for `xirr()`.

**Implementation**
- Solver: `scipy.optimize.newton`
- Initial guess:
  - -0.1 if total cashflows < 0
  - 0.1 otherwise
- Returns IRR as decimal (e.g., 0.1523 = 15.23%).

---
## Logging and Validation

All functions include integrated logging using the global project logger.

Key events recorded: invalid input lengths, sign convention issues, convergence results, and processing status.

Exceptions and warnings are automatically captured with full stack traces.

Log outputs are saved to the /logs/ directory for review (logs/project.log).

---
## Streamlit Dashboard

This Streamlit dashboard provides an interactive interface for the Private Credit Performance pipeline.
It allows users to apply a custom parallel shocks to the monthly interest rate data, trigger the underlying data-processing workflow, and visualize the resulting Gross vs. Net IRR chart on different levels.

### Live Demo
https://pcproject-txbae7crmzj9kvncbpzow7.streamlit.app/

### Overview
- Accepts a user-input interest rate shock (e.g., 0.01 = +100bps, -0.0025 = -25bps)
- Runs the same core pipeline as the command line version (`python -m irr_calc --shock <value>`)
- Displays process logs and the generated IRR chart
- Saves all outputs to the `outputs/` folder
### App Input
- choose the rates they want to shock the monthly intrest rate
### App Output
- The diagram showing the performance impacted by the shock

### How to Run Locally
1. Activate your virtual environment:
   - Windows PowerShell:
     .\venv\Scripts\Activate.ps1
   - macOS/Linux:
     source venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Launch the Streamlit app:
   streamlit run streamlit_app.py

### How It Works
1. User inputs an interest rate shock in the web interface.
2. The app executes the Python module `irr_calc` with the corresponding shock parameter.
3. The backend pipeline processes the input data, recalculates performance metrics, and generates a chart.
4. The app displays the updated Gross vs. Net IRR chart and saves it to `outputs/irr_plot.png`.
---

## Known Limitations and Future Improvements
- data only read from csv. Should connect to a database if data is fed daily
- Currency consistency QC (ensure EUR loans map to EUR curves)
- FX conversion between base and local IRR
- PIK verification QC
- Delayed-draw modeling refinements
- Deal/facility-level curve application
- End-market value and residual modeling
- Fund-level net IRR limited by lack of repayment data
- Management fee, tax, and accrued carry inclusion

---

**Author:** Yichen Zhou  
**Contact:** yichenzhou6@gmail.com
