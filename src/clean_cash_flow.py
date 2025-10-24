import numpy as np
import logging
import pandas as pd

logger = logging.getLogger("pc_project")

def cash_flow_sign_convert(cleaned_df : pd.DataFrame) -> pd.DataFrame:
    """
    Convert cash flow 'amount' signs based on cashflow_type conventions.

    This function ensures that all contribution-type cash flows are stored
    as negative values (representing capital outflows), while all other
    cash flow types—such as interest, principal return, PIK interest, and
    exit fees—are converted to positive values (representing inflows).

    Parameters
    ----------
    cleaned_df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        A new DataFrame with consistent sign conventions applied.

  """

    df = cleaned_df.copy()
    negative_list = ['contribution']

    # ---------------------------------------------------------------------
    # Sign convention adjustment
    # Ensures contributions are negative (capital outflow) and all others positive.
    # ---------------------------------------------------------------------
    if 'cashflow_type' not in df.columns or 'amount' not in df.columns:
        logger.error("Missing required columns: 'cashflow_type' or 'amount'. Sign conversion skipped.")
        return df

    mask_neg = df['cashflow_type'].isin(negative_list)
    neg_count = mask_neg.sum()
    pos_count = len(df) - neg_count

    df['amount'] = np.where(mask_neg, -df['amount'].abs(), df['amount'].abs())

    # ---------------------------------------------------------------------
    # Logging summary information
    # ---------------------------------------------------------------------
    logger.info("Applied cash flow sign convention.")
    logger.info(f"  • Negative cash flow types: {negative_list}")
    logger.info(f"  • Rows converted to negative: {neg_count}")
    logger.info(f"  • Rows converted to positive: {pos_count}")

    # Check a small sample for validation
    sample = df[['cashflow_type', 'amount']].head(5).to_string(index=False)
    logger.debug(f"Sample after sign conversion:\n{sample}")
    logger.info("-" * 70)

    return df
