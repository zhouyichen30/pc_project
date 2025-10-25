import pandas as pd
import logging

# this is your global logger
logger = logging.getLogger("pc_project")

def clean_leverage_df(leverage_df: pd.DataFrame) -> pd.DataFrame:
    """
    The purpose of this function is to clean the fund column so that it will be ready to merge.

    Parameters
    ----------
    leverage_df : pd.DataFrame
        DataFrame with a 'fund' column to clean.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with standardized fund names.
    """
    logger.info("Starting leverage_df fund name cleaning...")

    # Keep a copy to detect changes
    before = leverage_df['fund'].copy()

    # Normalize: lowercase, trim, replace multiple spaces/underscores
    leverage_df['fund'] = (
        leverage_df['fund']
        .astype(str)
        #replace to lower case
        .str.lower()
        .str.strip()
        #replace the underscore
        .str.replace(r'[\s_]+', '_', regex=True)
    )

    # Count changes
    changes = (before != leverage_df['fund']).sum()
    logger.info("Fund name cleaning completed. %d rows modified.", changes)

    # Optional debug log showing examples of changed rows
    if changes > 0:
        diff = leverage_df.loc[before != leverage_df['fund'], ['fund']].copy()
        diff['original'] = before[before != leverage_df['fund']]
        logger.debug("Sample cleaned fund names:\n%s", diff.head())

    return leverage_df
