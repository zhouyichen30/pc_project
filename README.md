Private Credit Performance – Technical Assessment

A reproducible Python workflow for ingesting, cleaning, and analyzing private credit cash flow data.
The goal is to normalize raw CSV inputs, compute XIRR/MOIC metrics, model leverage impact, and output a unified performance summary.

Setup Instructions
1) Clone the repository
git clone <your-repo-url>
cd pc_project

2) Create and activate a virtual environment
# Create
python -m venv venv

# Activate
# macOS/Linux
source venv/bin/activate
# Windows PowerShell
venv\Scripts\Activate.ps1

3) Install dependencies
pip install -r requirements.txt

Project Overview
Current Goal

Build an end-to-end, reproducible pipeline for analyzing private credit investments as part of a technical assessment.

Completed Components
Data Cleaning

Centralized clean_data() in src/utils.py:

Dates via pd.to_datetime(errors="coerce")

Strings via .str.strip().str.lower()

Numerics via pd.to_numeric(errors="coerce")

Logs unique values by text column for anomaly detection

Dataset-specific cleaners added for edge cases (e.g., curve label typos).

Data Integration

src/merge.py joins cleaned datasets:

cashflows_deal.csv ↔ terms.csv, structure.csv on facility_id

Linked to leverage.csv on fund

Uses outer joins to surface mismatches during debugging

Quality checks log missing and duplicate keys after each merge.

Curve Data

Fixed label inconsistencies (examples):

sofr       23
s0fr        1
euribor    23
eurib0r     1


Curves merged on fund-level cost_of_funds_curve, assuming fixed-rate financing for this exercise.

Cash Flow Adjustments

adjust_fees() applies day-one OID and origination fee adjustments to initial outflows.

_adjust_pik() removes accrued PIK interest (not paid in cash).

adjust_cash_flow() applies both before performance calculations.

Logging

Global logger name: pc_project

Logs include:

Input/output shapes

Cleaning and merge steps

NA/duplicate summaries

Text value distributions

Log file: logs/project.log

Modeling Assumptions
General

No base-currency conversion; IRR/MOIC reported in fund currency from structure.csv.

Provided cash flows are treated as fixed (per instructions).

Curves and Financing

Rates reset monthly.

Each cash flow uses the most recent curve rate on or before its date.

Curves merged at fund level via cost_of_funds_curve (all facilities in a fund share the same base curve).

With more time, curves would be merged at deal/facility level for granular rate modeling and sensitivity.

Fees and OID

OID and origination fees treated as day-one adjustments to initial outflows.

Implemented via adjust_fees() in cash_flow_adjust.py.

Example: for simplicity, Facility F002 (delayed draw) applies both fees on each contribution.

PIK Interest

PIK interest assumed accrued (capitalized) and removed from cash flow inputs prior to IRR/MOIC.

In production, a QC step should verify PIK classification before exclusion.

Delayed Draw (Facility F002)

Delayed-draw schedule observed:

First draw: 2023-02-15

Second draw: 2025-05-15

Interest appears to accrue on total notional rather than by draw date.

Ideally, interest between the two draw dates would reflect only the first-draw amount, and PIK would be adjusted on the second draw date.

Due to time constraints, this adjustment is not implemented; interest is treated as accruing on total notional.

Other Simplifications

No interest-rate floors modeled.

No currency-level QC or FX normalization.

covenants.csv not used.

Output
Main Output

performance_summary.csv with the following columns:

level,id,name,paid_in,distributed,gross_irr,gross_moic,net_irr,net_moic

Optional (if extended)

IRR distribution by strategy or fund

+100 bps rate-shock sensitivity

Known Limitations and Future Improvements

Currency consistency QC (e.g., ensure EUR loans map to EUR curves).

FX conversion for base vs. local IRR comparisons.

PIK verification QC before exclusion.

Delayed-draw modeling for interest and PIK by draw schedule.

Curve application at deal/facility level instead of fund-level approximation.

Running the Pipeline
python -m src.main


This will:

Read and clean all CSVs

Log cleaning and merge steps

Apply fee and PIK adjustments

Produce performance_summary.csv in the output directory

Example Project Structure
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


Author: Yichen Zhou
Contact: yichenzhou6 at gmail dot com