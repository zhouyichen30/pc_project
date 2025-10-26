# Private Credit Performance – Technical Assessment

A reproducible Python workflow for ingesting, cleaning, and analyzing private credit cash flow data.  
The goal is to normalize raw CSV inputs, compute XIRR/MOIC metrics, model leverage impact, and output a unified performance summary.

---

1.Clone the repository

git clone <your-repo-url>
cd pc_project

2. Create and activate a virtual environment

# Create
python -m venv .venv

# Activate
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

3.Install dependencies

pip install -U pip
pip install -r requirements.txt
pip install -e .


From the project root (pc_project/), navigate into the src directory first:
cd src

excuate python -m irr_calc

#intrest rate shock
You can “shock” the base-rate curve by an absolute decimal amount before metrics are computed.


| Parameter | Unit    | Example   | Meaning                    |
| --------- | ------- | --------- | -------------------------- |
| `--shock` | decimal | `0.01`    | **+100 bps** upward shock  |
|           |         | `-0.0025` | **–25 bps** downward shock |


## Project Overview

### Current Goal
Build an end-to-end, reproducible pipeline for analyzing private credit investments as part of a technical assessment.

---

## Completed Components

### Data Cleaning
- Centralized `clean_data()` in `src/utils.py`:
  - Converts date columns using `pd.to_datetime(errors="coerce")`
  - Normalizes text via `.str.strip().str.lower()`
  - Converts numeric fields using `pd.to_numeric(errors="coerce")`
  - Logs unique values for anomaly detection
- Dataset-specific cleaners added for edge cases (e.g., curve label typos).

### Data Integration
- `src/merge.py` joins cleaned datasets:
  - `cashflows_deal.csv` ↔ `terms.csv`, `structure.csv` on `facility_id`
  - Linked to `leverage.csv` on `fund`
  - Uses **outer joins** to surface mismatches during debugging
- Quality checks log missing and duplicate keys after each merge.

### Curve Data
Fixed label inconsistencies before merging:

```
sofr       23
s0fr        1
euribor    23
eurib0r     1
```

Curves are merged at the **fund-level** via `cost_of_funds_curve`, assuming fixed-rate financing for this exercise.

### Cash Flow Adjustments
- `adjust_fees()` applies day-one OID and origination fee adjustments to initial outflows.  
- `_adjust_pik()` removes accrued PIK interest (not paid in cash).  
- `adjust_cash_flow()` applies both before metrics calculations.

### Logging
- Global logger: `pc_project`
- Logs include:
  - Input/output shapes
  - Cleaning and merge steps
  - NA/duplicate summaries
  - Value distributions for text fields
- Log file: `logs/project.log`

---

## Metrics Helpers

### `_pic_calc(level, mdb)`
Computes **Paid-In Capital (PIC)** as the sum of negative cashflows (capital contributions).

**Inputs**
- `level`: column or list of columns to group by (e.g., "facility_id", "deal_id", "fund").
- `mdb`: merged dataset with at least `["amount", level]`.

**Output**
- DataFrame with `[level, "paid_in"]`, where `paid_in` remains negative (outflow).

**Notes**
- Uses `groupby(..., as_index=False)` so keys stay as columns.
- Returns join-ready output.
- Logs missing columns or empty results.

---

### `_dis_calc(level, mdb)`
Computes **Distributions** as the sum of positive cashflows (returns/inflows).

**Output**
- DataFrame `[level, "distr"]`, with `distr` positive.
- Same validation and logging pattern as `_pic_calc`.

---

## Metrics Aggregation

### `metrics(level, mdb)`
Aggregates all key performance metrics at the given level.

**Calculations**
- `paid_in`: total contributed capital (negative)
- `distr`: total distributed (positive)
- `MOIC`: `distr / abs(paid_in)`
- `xirr`: computed per unique entity using dated cashflows

**Rolling IRR Calculation Across Levels**
The IRR and MOIC are calculated in a **hierarchical roll-up** approach:
- **Level 3 (Entity Level):**  
  IRR is calculated for each facility or entity (`entity_id`, `deal_id`, `fund`) based on raw, dated cashflows.
- **Level 2 (Deal Level):**  
  Aggregates all facilities within a deal to measure deal-level performance by summing cashflows.
- **Level 1 (Fund Level):**  
  Rolls up all deal-level data to compute fund-level IRR and MOIC, representing the total portfolio return.

Each level uses identical logic — the difference is only in the grouping keys passed to `metrics()`.
## Merging All Levels and Exporting Results

The merge_deal_level(level_3_metrics_db, level_2_metrics_db, level_1_metrics_db) function combines and standardizes performance data across all hierarchy levels—Facility, Deal, and Fund—into a single, structured DataFrame. It first renames the distr column to distributed for consistency, then labels each input with its respective level (Facility, Deal, or Fund) and identifier (entity_id, deal_id, or fund). The function stacks all three levels vertically in the order Facility → Deal → Fund, ensuring that lower-level records appear first, which is essential for accurate IRR aggregation and waterfall-style calculations. During this process, it converts key numeric fields (paid_in, distributed, MOIC, and xirr) to numeric types to prevent type errors. Since only net metrics are available, it maps xirr to gross_irr and MOIC to gross_moic, leaving the net_irr and net_moic columns blank for potential future expansion. Finally, the function logs the total number of merged rows, the count of entries at each level, and a summary of any missing values using the project’s global pc_project logger.

### Example Usage
```python
# Merge all levels together
mldb = merge_deal_level(level_3_metrics_db, level_2_metrics_db, level_1_metrics_db)

# Write final merged dataset to CSV
mldb.to_csv(OUT_path / 'cleanned_net_irr_all_levels.csv', index=False)


**Example**
```python
# Level 3: Entity-level metrics
level_3 = ['entity_id', 'deal_id', 'fund']
level_3_metrics_db = metrics(level_3, mdc_cleanned)

# Level 2: Deal-level metrics
level_2 = ['deal_id', 'fund']
level_2_metrics_db = metrics(level_2, mdc_cleanned)

# Level 1: Fund-level metrics
level_1 = ['fund']
level_1_metrics_db = metrics(level_1, mdc_cleanned)

print(level_1_metrics_db)
```

**Sign Conventions**
- Contributions (outflows): negative  
- Distributions (returns): positive  
- Keep `paid_in` negative for IRR accuracy  
- Convert to positive only when exporting final results

---

## XNPV / XIRR Functions

### `_xnpv(rate, cashflows, dates)`
Computes the Net Present Value (NPV) for irregularly spaced cashflows, consistent with Excel’s XNPV.

**Formula**
```
NPV(r) = Σ [ CF_i / (1 + r)^((t_i - t_0)/365) ]
```

**Inputs**
- `rate`: discount rate in decimal form (e.g., 0.10 for 10%)
- `cashflows`: list of cash amounts (negative = outflows, positive = inflows)
- `dates`: matching list of cashflow dates

**Notes**
- Uses ACT/365 day count.
- `t_0` = earliest date in the cashflow series.
- Raises a ValueError if input lengths mismatch.

**Purpose**
- Used as f(r) in Newton’s method for `xirr()`.

---

### `xirr(cashflows, dates)`
Computes the Internal Rate of Return (IRR) for irregularly spaced cashflows using Newton’s method on `_xnpv()`.

**Implementation**
- Solver: `scipy.optimize.newton`
- Initial guess:
  - `-0.1` if total cashflows < 0
  - `0.1` otherwise
- Returns IRR as a decimal (e.g., 0.1523 = 15.23%)

**Logging and Validation**
- Logs warnings for invalid inputs:
  - Unequal lengths of cashflows and dates
  - All cashflows of same sign
- Logs info when convergence succeeds, warning when it fails
- Returns `None` if Newton fails to converge

**Sign Convention**
- Contributions: negative  
- Distributions: positive  
- Day count: ACT/365

---

## Modeling Assumptions

### General
- No base-currency conversion; IRR/MOIC in fund currency from `structure.csv`.
- Provided cashflows are treated as fixed (per instructions).

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
- In a full model, interest and PIK would adjust per draw schedule.

### fundlevel financing assume
 - Drawn Amount — Each capital contribution is treated as a draw on the fund’s credit facility:
   - drawn = contribution_amount × advance_rate
 - Credit Line Size — Each fund’s total credit line is set at 20% of total committed capital:
   - credit_line = commitment × 0.20
 - Undrawn Balance Logic

    For the first draw per fund, the undrawn balance is reduced by the amount drawn:
    undrawn = credit_line + finance_portion
    (e.g., if credit_line = 80M and first draw = –60.95M → undrawn = 19.05M)

    For subsequent draws or repayments, the undrawn reflects the period’s net movement only:
    undrawn = finance_portion
    (e.g., a second draw of –2.96M represents a further use of the credit line.)

 - Repayment Timing — The credit line is assumed to be fully repaid at the fund’s exit_date.
   All facilities in this exercise have exit events, so repayment is aligned with that timing.

 - Cost of Funds Spread (bps) and Undrawn Fee (bps) are modeled as annualized rates.

 - Both are accrued monthly, based on the outstanding drawn and undrawn balances at each period.

 - These parameters will later be merged with the relevant curve data (e.g., SOFR, EURIBOR) to compute:

 - fund level Interest Expense: drawn × ((curve_rate + spread_bps)/10,000) × days/360

 - Undrawn Fee Expense: undrawn × (undrawn_fee_bps/10,000) × days/360

 - Payment date rule: cash interest/fees are paid on the 15th of the following month (e.g., 2023-02-28 → 2023-03-15).
 
 - Month-end expansion window: only include month-ends ≥ con_date and ≤ exit_date; anything outside is dropped.
 
 - First period anchor: the first period starts from the prior month-end of con_date for rate alignment; curve is joined on month-end dates.
 - no working days are considered in this model
 - no floor on the credit line rates

 # Apply shock

 -when shock the interest rate, intrest rate cannot goes to negtive 

### net irr
# paid in capital are treat as negtive
# dirtubution are reate as postive
# expense 

### Other Simplifications
- No interest-rate floors.
- No currency-level QC or FX normalization.
- `covenants.csv` not used.

---

## Output

### Main Outputs
in cash_master folder
- `cleanned_cashflow_master.csv` – fully cleaned and merged data prior to modeling  
-'cleanned_cashflow_master_fund_added.csv' - cleanned data with fund level expense added to calculate net irr

- `cleanned_net_irr_all_level.csv` - output from second steps before fund irr calc -used for qc
- `performance_summary.csv` – the output contrains level (Facility/Deal/Fund), id, name, paid_in, distributed, gross_irr, gross_moic, net_irr, net_moic.
  `fund_info.csv` — cleaned fund-level dataset aggregated from raw cashflows before joining with curve data.
  Contains each fund’s contribution, financing portion, undrawn balance, and commitment structure.

  `fund_curve.csv` — fund-level data joined with monthly curve rates (e.g., SOFR, EURIBOR).
  Includes calculated fields such as all_in_rate and undrawn_fee_rate, along with the corresponding month-end and payment dates.

  `fee_calc.csv` — monthly output showing each fund’s interest and undrawn fee cashflows.
  Generated using the drawn (finance_portion) and undrawn amounts with their respective annualized rates (divided by 12 for monthly accrual).
- 'irr_plot.png' - This chart visualizes Gross vs. Net IRR across Facility, Deal, and Fund levels, with percentage labels on each bar and black dashed rectangles highlighting each hierarchy level.


## Known Limitations and Future Improvements
- Currency consistency QC (e.g., ensure EUR loans map to EUR curves)
- FX conversion for base vs. local IRR
- PIK verification QC before exclusion
- Delayed-draw modeling for interest and PIK by schedule
- Curve application at deal/facility level instead of fund approximation
- End-market value analysis
- Fund level net irr calc is limited due to no credit line payment data
- mangement fee, tax, accured carry need to be inculded in net irr

---

## Running the Pipeline
```bash
python -m src.main
```

This will:
- Read and clean all CSVs  
- Log all steps  
- Apply OID and PIK adjustments  
- Compute metrics and IRR  
- Output `performance_summary.csv` in `outputs/`

---

## Example Project Structure
```
pc_project/
├─ data/
│  ├─ cashflows_deal.csv
│  ├─ structure.csv
│  ├─ terms.csv
│  ├─ leverage.csv
│  └─ curves.csv
├─ logs/
│  └─ project.log
├─ outputs/
│  └─ performance_summary.csv
├─ src/
│  ├─ main.py
│  ├─ utils.py
│  ├─ merge.py
│  ├─ cash_flow_adjust.py
│  ├─ clean_cash_flow.py
│  ├─ clean_curve.py
│  └─ clean_structure.py
├─ requirements.txt
└─ README.md
```

---

**Author:** Yichen Zhou  
**Contact:** yichenzhou6 at gmail dot com
##
Running main.py executes the full data-processing pipeline:

Data ingestion — reads raw CSV files from data/

Cleaning & formatting — applies standardized date, text, and numeric conversions

Merging & adjustments — joins term, structure, leverage, and curve data; adjusts cashflows

Metric computation — calculates Paid-In, Distributions, Gross IRR/MOIC, and Net IRR/MOIC across Facility → Deal → Fund levels

Visualization — produces irr_plot.png comparing Gross vs. Net IRR by level

All processing steps, shapes, and intermediate validations are recorded in a unified log file:

logs/project.log


Each entry includes timestamp, log level, and module source, for example:

2025-10-26 16:57:23,083 [INFO] pc_project.metrics: Computing metrics at level: ['entity_id', 'facility_name', 'deal_id', 'fund']
2025-10-26 16:57:23,476 [INFO] pc_project.fund_metrics: Pipeline finished successfully. Outputs saved in: outputs/fund_level
2025-10-26 16:57:24,683 [INFO] pc_project.charts: Chart saved to: outputs/irr_plot.png


This makes it easy to trace every operation—from initial data cleaning through final IRR chart generation—directly in the log file.
