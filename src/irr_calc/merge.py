import pandas as pd
import logging

#import logger 
logger = logging.getLogger(__name__)

def merge_db(
    cashflow_df: pd.DataFrame,
    term_df: pd.DataFrame,
    structure_df: pd.DataFrame,
    leverage_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge cashflow, term, structure, and leverage datasets into one DataFrame.

    Relationships:
        cashflow_df.entity_id      = structure_df.facility_id
        structure_df.facility_id   = term_df.facility_id
        structure_df.fund          = leverage_df.fund

    Parameters
    ----------
    cashflow_df : pd.DataFrame
        Cleaned cashflow dataset.
    term_df : pd.DataFrame
        Cleaned term dataset.
    structure_df : pd.DataFrame
        Cleaned structure dataset.
    leverage_df : pd.DataFrame
        Cleaned leverage dataset.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame combining all datasets.
    """
    logger.info("Starting merge pipeline...")

    logger.debug(
        "Input shapes | cashflow=%s | terms=%s | structure=%s | leverage=%s",
        cashflow_df.shape,
        term_df.shape,
        structure_df.shape,
        leverage_df.shape,
    )

    # --- 1) Cashflow ⟶ Structure (entity_id -> facility_id)
    logger.info("Before structure merge: %s", cashflow_df.shape)
    merged = cashflow_df.merge(
        structure_df,
        how="outer",
        left_on="entity_id",
        right_on="facility_id",
        suffixes=("", "_struct"),
    )
    logger.info("After structure merge: %s", merged.shape)

    # --- 2) Cashflow ⟶ Terms (entity_id -> facility_id)
    merged = merged.merge(
        term_df,
        how="outer",
        left_on="entity_id",
        right_on="facility_id",
        suffixes=("", "_term"),
    )
    logger.info("After terms merge: %s", merged.shape)

    # --- 3) Structure ⟶ Leverage (fund -> fund)
    merged = merged.merge(
        leverage_df,
        how="outer",
        on="fund",
        suffixes=("", "_lev"),
    )
    logger.info("After leverage merge: %s", merged.shape)

    # --- Data Quality Checks ---
    #Check for missing values
    na_counts = merged.isna().sum()
    total_na = int(na_counts.sum())
    if total_na > 0:
        logger.warning("Detected %d total missing values across %d columns.", total_na, (na_counts > 0).sum())
        logger.debug("NaN breakdown (top 10 columns):\n%s", na_counts.sort_values(ascending=False).head(10).to_string())
    else:
        logger.info("No missing values detected in merged dataset.")

    # Check for duplicate rows
    dup_count = int(merged.duplicated().sum())
    if dup_count > 0:
        logger.warning("Detected %d duplicate rows in merged dataset.", dup_count)
        logger.debug("Sample duplicate rows:\n%s", merged[merged.duplicated()].head(5).to_string(index=False))
    else:
        logger.info("No duplicate rows detected in merged dataset.")

    logger.info("Merge pipeline completed. Final shape: %s", merged.shape)
    return merged

def merge_curve(mdb: pd.DataFrame, curvedb: pd.DataFrame) -> pd.DataFrame:
    """
    Merge monthly base-rate curve data into the main dataset.

    Purpose
    -------
    To associate each cashflow record with the corresponding base-rate curve 
    used for its financing cost. Since rates reset monthly, each cashflow 
    is matched to the prior month-end rate for its designated curve.

    Assumptions
    -----------
    - Both `mdb['asof']` and `curvedb['asof']` are datetime columns.
    - Interest rates reset monthly; each cashflow references the 
    previous month-end rate.
    - Merge keys: ('cost_of_funds_curve', last month-end date).

    Procedure
    ---------
    1. Derive a new column `asof_mend` = previous month-end for each cashflow.
    2. Merge the main dataset (`mdb`) with the curve dataset (`curvedb`) 
    using ('cost_of_funds_curve', 'asof_mend') ↔ ('curve', 'asof').
    3. Log and inspect unmatched rows (e.g., top 5 with missing curve data).
    4. Return the merged DataFrame containing the matched curve rate.

    Parameters
    ----------
    mdb : pd.DataFrame
        Main dataset containing columns ['asof', 'cost_of_funds_curve'].
    curvedb : pd.DataFrame
        Curve dataset with columns ['curve', 'asof', 'rate'].

    Returns
    -------
    pd.DataFrame
        The merged DataFrame with the corresponding monthly curve rate appended.
    """

    # 1) compute last month-end on mdb
    mdb['asof_mend'] = mdb['asof'] - pd.offsets.MonthEnd(1)

    # 2) merge curves (previous month-end rate)
    merged = mdb.merge(
        curvedb,
        left_on=['cost_of_funds_curve', 'asof_mend'],
        right_on=['curve', 'asof'],
        how='left',
        suffixes=('', '_curve')
    )

    # 3) Log summary of missing curve matches
    na_mask = merged['rate'].isna()
    na_count = na_mask.sum()
    if na_count > 0:
        logger.warning("Curve merge: %d unmatched rows (no curve rate found).", na_count)
        logger.debug("Top 5 unmatched rows:\n%s",
                     merged.loc[na_mask, ['asof_mend', 'cost_of_funds_curve', 'entity_id']].head(5).to_string(index=False))
    else:
        logger.info("Curve merge successful: all rows matched a curve rate.")

    return merged