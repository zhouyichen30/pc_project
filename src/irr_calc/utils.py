import pandas as pd
import logging
from pathlib import Path

# -------------------------------------------------------------------
# Global logger setup — shared across all utility functions
#logger will write to logs folder under PC_PROJECT
# -------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "project.log"  # single file for all logs

logging.basicConfig(
    level=logging.INFO,
    #example logger format: 2025-10-23 22:09:27,782 [INFO] pc_project: Starting data cleaning.
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# This logger will be used by all functions in utils.py
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# function 1: clean_data
# -------------------------------------------------------------------
def clean_data_format(data : pd.DataFrame, date_cols : list, text_cols :list, num_cols:list ) -> pd.DataFrame:
    """
    Clean a pandas DataFrame and output a cleaned DataFrame that has correct
    data types and standardized formatting for each category of columns.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing raw data.
    date_cols : list
        List of column names in 'data' that should be converted to datetime.
    text_cols : list
        List of column names in 'data' that should be stripped of whitespace
        and converted to lowercase for consistency.
    num_cols : list
        List of column names in 'data' that should be coerced to numeric type.

    Returns
    -------
    pd.DataFrame
        A cleaned copy of the original DataFrame with normalized formats.
    """
    df = data.copy()
    

    logger.info("Starting data cleaning.")
    logger.info(f"Input shape: {df.shape}")
    
    #make sure all columns dont have leading or trailing spaces
    df.columns = df.columns.str.strip()

    # 1. Convert date columns
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            logger.debug(f"Converted '{col}' to datetime format.")
        else:
            logger.warning(f"Date column '{col}' not found in DataFrame.")

    # 2. Clean text columns
    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                # remove leading/trailing white space
                .str.strip()
                #make sure all data are lowered case
                .str.lower()
                 # replace multiple spaces or underscores with a single underscore
                .str.replace(r'[\s_]+', '_', regex=True)
                
            )
            logger.debug(f"Cleaned text column '{col}'.")
            
        else:
            logger.warning(f"Text column '{col}' not found in DataFrame.")

    # 3. Convert numeric columns
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            logger.debug(f"Converted '{col}' to numeric type.")
            #we then filiter out missing na value for numeric columns as 0
            df[col] = df[col].fillna(0)
        else:
            logger.warning(f"Numeric column '{col}' not found in DataFrame.")
            
    # Drop rows with missing key fields (dates or numeric amounts)
    # and log how many were removed. Keeps it straightforward.
    # ---------------------------------------------------------------------
    #this part handing na
    before = len(df)
    #find the na row
    na_rows = df[df.isna().any(axis=1)]
    #logging na row so we know what roles the code dropped
    if not na_rows.empty:
        logger.info(f"Rows containing NaN values (showing up to 5):\n{na_rows.head(5).to_string(index=False)}")
    else:
        logger.info("No NaN values detected in the dataset.")
    #dorpping na row for date only
    df = df.dropna(subset=date_cols)

    logger.info("Data cleaning complete.")
    logger.info(f"Output shape: {df.shape}")
    logger.info("-" * 50)
        # ---------------------------------------------------------------------
    # Summary of cleaned text columns
    #   Logs high-level stats for each text column after cleaning:
    #   total rows, number of unique values, null/empty counts, and
    #   top 5 most frequent values. Helps verify normalization results.
    # ---------------------------------------------------------------------
    for col in text_cols:
        if col in df.columns:
            #find teh top 7 unique values for each text columns and logg these so I can always debug data error
            top_values = df[col].value_counts().head(7)
            logger.info(f"Top values in '{col}':\n{top_values.to_string()}")
            logger.info("-" * 50)
    return df

def stack_fund_fees_into_master(fees: pd.DataFrame, master_cashflow: pd.DataFrame) -> pd.DataFrame:
    """
    Align and append fund-level fee cashflows to the master cashflow table.

    Parameters
    ----------
    fees : pd.DataFrame
        Fund-level fees with columns:
        ['payment_date', 'cashflow_type', 'fund', 'amount'].
    master_cashflow : pd.DataFrame
        Existing master cashflow table with schema like:
        ['asof','entity_id','entity_type','cashflow_type','amount','currency',...,'fund',...].

    Returns
    -------
    pd.DataFrame
        Combined table with master schema; fund rows appended with
        non-applicable fields left as NaN.
    """
    # Rename to match master schema
    fees_aligned = fees.rename(columns={'payment_date': 'asof'}).copy()

    # Add any missing columns dynamically (no manual listing)
    for col in master_cashflow.columns:
        if col not in fees_aligned.columns:
            fees_aligned[col] = pd.NA

    # Reorder columns to match master
    fees_aligned = fees_aligned[master_cashflow.columns]

    # Stack together
    combined = pd.concat([master_cashflow, fees_aligned], ignore_index=True)

    # Logging
    logger.info(
        "stack_fund_fees_into_master: appended %d fund rows to %d master rows (total=%d).",
        len(fees_aligned), len(master_cashflow), len(combined)
    )

    return combined