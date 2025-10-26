import pandas as pd
import logging
import numpy as np
logger = logging.getLogger("pc_project")

def clean_data_fund(mdc_cleanned: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a cleaned fund-level dataset from raw cashflows.

    Parameters
    ----------
    mdc_cleanned : pd.DataFrame
        Source dataset containing at least the following columns:
        ['entity_id', 'cashflow_type', 'asof', 'amount', 'commitment',
         'cost_of_funds_curve', 'spread_bps_lev', 'undrawn_fee_bps', 'advance_rate'].

    Returns
    -------
    pd.DataFrame
        A DataFrame with one row per entity_id including:
        ['entity_id', 'con_date', 'con_amount', 'fund_commitment',
         'cost_of_funds_curve', 'fund_spread_bps_lev', 'fund_undrawn_fee_bps',
         'advance_rate', 'finance_portion', 'credit_line', 'undrawn', 'exit_date'].
    """
    # Filter contribution and exit rows
    con_data = mdc_cleanned[mdc_cleanned['cashflow_type'] == 'contribution'].copy()
    exit_data = (
        mdc_cleanned[mdc_cleanned['cashflow_type'] == 'exit_fee'][['entity_id', 'asof']]
        .rename(columns={'asof': 'exit_date'})
        .copy()
    )

    # Assemble key fund-level columns from contribution data
    df = pd.DataFrame()
    df['entity_id']            = con_data['entity_id']
    df['con_date']             = con_data['asof']
    df['con_amount']           = con_data['amount']
    df['fund_commitment']      = con_data['commitment']
    df['cost_of_funds_curve']  = con_data['cost_of_funds_curve']
    df['fund_spread_bps_lev']  = con_data['spread_bps_lev']
    df['fund_undrawn_fee_bps'] = con_data['undrawn_fee_bps']
    df['advance_rate']         = con_data['advance_rate']
    df['fund'] = con_data['fund']
    

    # Calculate financed and undrawn amounts
    #apply advance rate on contribution amt
    df['finance_portion'] = df['con_amount'] * df['advance_rate']
    #we assume creditline total is 20% of the fund commitment
    df['credit_line'] = df['fund_commitment'] * 0.2

    # Merge exit dates
    df = df.merge(exit_data, on='entity_id', how='left')

    # Simple logging summary
    logger.info(f"clean_data_fund: processed {len(df)} records.")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Missing values summary: {df.isna().sum().to_dict()}")

    return df


def return_fund_info(fund_db: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate fund-level financing info by date with undrawn logic:
    - First draw per fund: undrawn = credit_line + finance_portion
    - Subsequent draws:    undrawn = finance_portion

    Parameters
    ----------
    fund_db : pd.DataFrame
        From clean_data_fund(); must include:
        ['fund','con_date','exit_date','finance_portion','credit_line',
         'cost_of_funds_curve','fund_spread_bps_lev','fund_undrawn_fee_bps','advance_rate']

    Returns
    -------
    pd.DataFrame
        Aggregated per fund and date:
        ['fund','con_date','exit_date','finance_portion','undrawn','credit_line',
         'cost_of_funds_curve','fund_spread_bps_lev','fund_undrawn_fee_bps','advance_rate']
    """
    fund_level = (
        fund_db.groupby(['fund', 'con_date', 'exit_date'], as_index=False)
        .agg({
            'finance_portion': 'sum',
            'credit_line': 'first',
            'cost_of_funds_curve': 'first',
            'fund_spread_bps_lev': 'first',
            'fund_undrawn_fee_bps': 'first',
            'advance_rate': 'first',
        })
    ).sort_values(['fund', 'con_date'])

    # Mark first draw per fund
    first_mask = fund_level.groupby('fund').cumcount() == 0

    # Undrawn logic:
    # first row → credit_line + finance_portion
    # others    → finance_portion
    fund_level['undrawn'] = np.where(
        first_mask,
        fund_level['credit_line'] + fund_level['finance_portion'],
        fund_level['finance_portion']
    )

    logger.info(
        "return_fund_info: aggregated %d rows for %d funds.",
        len(fund_level), fund_level['fund'].nunique()
    )

    return fund_level[[
        'fund','con_date','exit_date',
        'finance_portion','undrawn','credit_line',
        'cost_of_funds_curve','fund_spread_bps_lev','fund_undrawn_fee_bps','advance_rate'
    ]]




def expand_and_join_curve(fund_level: pd.DataFrame, curvedb: pd.DataFrame) -> pd.DataFrame:
    """
    Join monthly curve data to each fund between previous month-end(con_date) and month-end(exit_date),
    and compute simple rate columns.

    Parameters
    ----------
    fund_level : pd.DataFrame
        Clean fund-level data with at least:
        ['fund', 'con_date', 'exit_date', 'cost_of_funds_curve',
         'fund_spread_bps_lev', 'fund_undrawn_fee_bps',
         'finance_portion', 'undrawn'].
    curvedb : pd.DataFrame
        Monthly curve points:
        ['asof', 'curve', 'rate'] (asof should be month-end).

    Returns
    -------
    pd.DataFrame
        One row per fund × month_end with:
        ['fund', 'con_date', 'exit_date', 'month_end','payment_date',
         'cost_of_funds_curve', 'rate', 'all_in_rate',
         'fund_spread_bps_lev', 'fund_undrawn_fee_bps', 'undrawn_fee_rate',
         'finance_portion', 'undrawn'].

    Notes
    -----
    - all_in_rate = curve rate + (fund_spread_bps_lev / 10,000)
    - undrawn_fee_rate = fund_undrawn_fee_bps / 10,000
    - This step does not compute day-count accruals; it only prepares monthly rates.
    - we assume all the interest charge on 15th of each month
    """
    fl = fund_level.copy()
    fl['start_me'] = pd.to_datetime(fl['con_date']) + pd.offsets.MonthEnd(-1)
    fl['exit_me']  = pd.to_datetime(fl['exit_date']) + pd.offsets.MonthEnd(0)

    # Expand month-end range
    fl['month_end'] = fl.apply(lambda r: pd.date_range(r['start_me'], r['exit_me'], freq='ME'), axis=1)
    fl = fl.explode('month_end', ignore_index=True)

    # Join curve
    curves = curvedb.rename(columns={'asof': 'month_end'}).copy()
    curves['month_end'] = pd.to_datetime(curves['month_end'])
    out = fl.merge(
        curves[['curve', 'month_end', 'rate']],
        left_on=['cost_of_funds_curve', 'month_end'],
        right_on=['curve', 'month_end'],
        how='left'
    ).drop(columns=['curve'])

    # Compute rates
    out['all_in_rate'] = out['rate'] + (out['fund_spread_bps_lev'] / 10_000)
    out['undrawn_fee_rate'] = out['fund_undrawn_fee_bps'] / 10_000

    #drop month end data not in the date range of con and exit date
    out = out[(out['month_end'] >= out['con_date']) & (out['month_end'] <= out['exit_date'])]
    #convert a payment date, example 2023-02-28 → 2023-03-15
    out['payment_date'] = (out['month_end'] + pd.offsets.MonthBegin(1)) + pd.DateOffset(days=14)



    # Reorder columns
    out = out[[
        'fund', 'con_date', 'exit_date', 'month_end','payment_date',
        'cost_of_funds_curve', 'rate', 'all_in_rate',
        'fund_spread_bps_lev', 'fund_undrawn_fee_bps', 'undrawn_fee_rate',
        'finance_portion', 'undrawn'
    ]]

    logger.info(
        "expand_and_join_curve: produced %d fund×month rows across %d funds.",
        len(out), out['fund'].nunique()
    )
    logger.info(
        "expand_and_join_curve: missing curve rates on %d rows.",
        out['rate'].isna().sum()
    )



    return out

def calc_monthly_fee(fund_level_curve: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate monthly interest and undrawn fee cashflows for each fund.

    Parameters
    ----------
    fund_level_curve : pd.DataFrame
        Must include:
        ['fund', 'payment_date', 'finance_portion', 'undrawn',
         'all_in_rate', 'undrawn_fee_rate'].

    Returns
    -------
    pd.DataFrame
        A DataFrame with:
        ['payment_date', 'cashflow_type', 'fund', 'amount'].
        Each month generates two rows per fund:
        one for 'interest' and one for 'undrawn_fee'.
    """
    out = fund_level_curve.copy()

    # Calculate fund-level interest and undrawn fee cashflows (monthly accrual = rate / 12)
    fees = pd.concat([
        out.assign(
            cashflow_type='interest',
            amount=out['finance_portion'] * out['all_in_rate'] / 12
        ),
        out.assign(
            cashflow_type='undrawn_fee',
            #times negtive 1 - so we can treat the second draw as a postive cashflow that paydown the undrwan fees
            amount=out['undrawn'] * out['undrawn_fee_rate'] / 12 *-1
        )
    ])[['payment_date', 'cashflow_type', 'fund', 'amount']]

    # Logging summary
    logger.info(
        "calc_monthly_fee: generated %d fee rows across %d funds.",
        len(fees), fees['fund'].nunique()
    )
    logger.info(
        "calc_monthly_fee: interest rows=%d, undrawn_fee rows=%d",
        (fees['cashflow_type'] == 'interest').sum(),
        (fees['cashflow_type'] == 'undrawn_fee').sum()
    )

    return fees

def run_fund_level_pipeline(mdc_cleanned: pd.DataFrame,
                            curve_df_cleaned: pd.DataFrame,
                            OUT_path: str) -> None:
    """
    Run the full fund-level financing pipeline:
    1. Clean raw cashflows
    2. Aggregate to fund-level
    3. Join curve data
    4. Calculate monthly interest and undrawn fees
    5. Export results to the existing /fund_level folder

    Parameters
    ----------
    mdc_cleanned : pd.DataFrame
        Raw input dataset containing:
        ['entity_id','cashflow_type','asof','amount','commitment',
         'cost_of_funds_curve','spread_bps_lev','undrawn_fee_bps','advance_rate'].
    curve_df_cleaned : pd.DataFrame
        Monthly curve data with columns:
        ['asof','curve','rate'] (month-end points).
    OUT_path : pathlib.Path
        Existing output directory containing /fund_level subfolder.

    Returns
    -------
    None
        Writes the following CSVs under OUT_path / "fund_level":
        - fund_info.csv
        - fund_curve.csv
        - fee_calc.csv
    """
    logger.info("Starting full fund-level financing pipeline...")

    # Define output folder (already exists)
    out_dir = OUT_path / "fund_level"

    # Step 1: Clean raw data
    fund_db = clean_data_fund(mdc_cleanned)
    logger.info("Step 1: clean_data_fund complete — %d rows", len(fund_db))

    # Step 2: Aggregate to fund-level
    fund_level_info = return_fund_info(fund_db)
    fund_level_info.to_csv(out_dir / 'fund_info.csv', index=False)
    logger.info("Step 2: return_fund_info complete — %d rows", len(fund_level_info))

    # Step 3: Join with curve data
    fund_level_curve = expand_and_join_curve(fund_level_info, curve_df_cleaned)
    fund_level_curve.to_csv(out_dir / 'fund_curve.csv', index=False)
    logger.info("Step 3: expand_and_join_curve complete — %d rows", len(fund_level_curve))

    # Step 4: Calculate monthly interest + undrawn fee cashflows
    fees = calc_monthly_fee(fund_level_curve)
    fees.to_csv(out_dir / 'fee_calc.csv', index=False)
    logger.info("Step 4: calc_monthly_fee complete — %d rows", len(fees))

    logger.info("Pipeline finished successfully. Outputs saved in: %s", out_dir)
    return fees
