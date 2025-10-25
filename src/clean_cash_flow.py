import numpy as np
import logging
import pandas as pd

#this script contains all the funcations to clean the cashflows_deal.csv 

logger = logging.getLogger("pc_project")

def _clean_entity_id(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """"
    Normalize entity_id values (e.g., convert 'fo02' -> 'f002').

    Parameters
    ----------
    cleaned_df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        A new DataFrame with make sure entity_id is converted
    """
    # replace all o to 0
    cleaned_df['entity_id'] = cleaned_df['entity_id'].str.replace('o', '0')
    logger.info(f"entity_id clean complete - cleaned db: {cleaned_df['entity_id'].value_counts()}")
    return cleaned_df


def _cash_flow_sign_convert(cleaned_df : pd.DataFrame) -> pd.DataFrame:
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

def cash_flow_clean(cleaned_df : pd.DataFrame) -> pd.DataFrame:
    """
    This funcation is a wrapper that do cashflow clean for cashflow_deal.csv

    Parameters
    ----------
    cleaned_df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        apply all the models to make sure cash_flow_data is cleanned

    
    """
    cleaned_df = _clean_entity_id(cleaned_df)
    cleaned_df = _cash_flow_sign_convert(cleaned_df)

    return cleaned_df
