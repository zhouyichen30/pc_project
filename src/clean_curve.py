import pandas as pd
import logging

logger = logging.getLogger("pc_project")

def clean_curve_df(curve_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans curve names such as 's0fr' -> 'sofr' and 'eurib0r' -> 'euribor'.

    Example input:
        curve
        sofr       23
        euribor    23
        eurib0r     1
        s0fr        1

    Parameters
    ----------
    curve_df : pd.DataFrame
        DataFrame with a 'curve' column to clean.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with standardized curve names.
    """
    logger.info("Starting curve cleaning process...")

    # Snapshot of before counts
    before_counts = curve_df['curve'].value_counts(dropna=False)
    logger.debug("Before cleaning value counts:\n%s", before_counts)
    
    cleaned_df = curve_df.copy()
    #make sure all the type is cleaned
    cleaned_df['curve'] = (
        cleaned_df['curve']
        .astype(str)
        .str.lower()
        .str.replace('0', 'o', regex=True)
        .replace({'eurib0r': 'euribor', 'sofr': 'sofr'}, regex=True)
        .str.strip()
    )

    # Compare before/after
    after_counts = cleaned_df['curve'].value_counts(dropna=False)
    logger.debug("After cleaning value counts:\n%s", after_counts)

    # Count number of rows modified
    changes = (curve_df['curve'].astype(str).str.lower() != cleaned_df['curve']).sum()
    #write value counts after claen
    curve_data_value = cleaned_df['curve'].value_counts()
    logger.info("Curve cleaning completed — %d values modified.", changes)
    logger.info(f'curve data after cleaned {curve_data_value}')

    return cleaned_df
