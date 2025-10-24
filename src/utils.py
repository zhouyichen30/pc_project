import pandas as pd
import logging
from pathlib import Path

# -------------------------------------------------------------------
# Global logger setup — shared across all utility functions
#logger will write to logs folder under PC_PROJECT
# -------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
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
logger = logging.getLogger("pc_project")

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
        else:
            logger.warning(f"Numeric column '{col}' not found in DataFrame.")
            
    # Drop rows with missing key fields (dates or numeric amounts)
    # and log how many were removed. Keeps it straightforward.
    # ---------------------------------------------------------------------
    before = len(df)
    df = df.dropna(subset=date_cols + num_cols)
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} malformed rows with missing date or amount values.")
    else:
        logger.info("did not drop any missing values.")
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
            top_values = df[col].value_counts().head(5)
            logger.info(f"Top values in '{col}':\n{top_values.to_string()}")
            logger.info("-" * 50)
    return df