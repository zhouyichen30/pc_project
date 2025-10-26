import logging
import pandas as pd

#this script contains all the funcations to clean the cashflows_deal.csv 

logger = logging.getLogger(__name__)

def _adjust_fees(merged_db: pd.DataFrame) -> pd.DataFrame:
    """
    Apply OID and origination fee adjustments to the initial investment cashflow.

    Both OID and origination fees are treated as day-one yield adjustments:
    - OID reduces the amount funded (the borrower receives less than par).
    - Origination fee offsets part of the investment outflow.

    Parameters
    ----------
    merged_db : pd.DataFrame
        Must include columns ['amount', 'OID_bps', 'origination_fee_bps'].

    Returns
    -------
    pd.DataFrame
        Adjusted DataFrame with updated 'amount' reflecting OID and fee effects.
    """
    df = merged_db.copy()
    if not {'amount', 'OID_bps', 'origination_fee_bps'}.issubset(df.columns):
        logger.warning("Missing columns for OID/origination fee adjustment.")
        return df

    df[['OID_bps', 'origination_fee_bps']] = df[['OID_bps', 'origination_fee_bps']].fillna(0)

    # Track total invested before and after adjustment
    total_before = df.loc[df['amount'] < 0, 'amount'].sum()
    df.loc[df['amount'] < 0, 'amount'] *= (
        1 - (df['OID_bps'] + df['origination_fee_bps']) * 0.0001
    )
    total_after = df.loc[df['amount'] < 0, 'amount'].sum()

    logger.info(f"Adjusted OID/origination fees for {(df['amount'] < 0).sum()} cashflows.")
    logger.info(f"Total invested before: {total_before:,.2f} | after adjustment: {total_after:,.2f}")

    return df

def _adjust_pik(merged_db: pd.DataFrame) -> pd.DataFrame:
    """
    Remove Payment-in-Kind (PIK) interest cashflows from the dataset.

    Assumption
    ----------
    Based on inspection, all PIK interest entries in this dataset are accrued
    (i.e., capitalized into principal rather than paid in cash). For this
    exercise, these PIK cashflows are excluded from IRR and MOIC calculations.

    Note
    ----
    In a production setting, a quality-control step should be added to verify
    that all 'pik_interest' records are correctly tagged and properly rolled
    into principal rather than simply removed.
    """
    df = merged_db.copy()

    if 'cashflow_type' not in df.columns:
        logger.warning("Column 'cashflow_type' not found — skipping PIK adjustment.")
        return df

    before_rows = len(df)
    df = df[df['cashflow_type'] != 'pik_interest']
    after_rows = len(df)

    logger.info(f"Removed {before_rows - after_rows} PIK interest cashflows (accrued).")

    return df

def adjust_cash_flow(merged_db: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all deal-level cashflow adjustments (PIK and fees).

    This function standardizes and cleans the main cashflow dataset by:
    1. Removing accrued PIK interest cashflows that are not paid in cash.
    2. Applying OID and origination fee adjustments to initial outflows
       to reflect day-one yield effects before IRR/MOIC calculation.

    Assumptions
    -----------
    - All 'pik_interest' entries are accrued (capitalized) and therefore removed.
    - OID and origination fees are treated as upfront adjustments to the
      initial investment cashflows.
    - Delayed-draw facilities (e.g., F002) remain unadjusted due to time
      constraints, with interest assumed to accrue on total notional.

    Returns
    -------
    pd.DataFrame
        The adjusted cashflow dataset ready for performance calculations.
    """
    df = merged_db.copy()

    df = _adjust_pik(df)
    df = _adjust_fees(df)

    return df
