import pandas as pd
import logging
from pathlib import Path

# -------------------------------------------------------------------
# Global logger setup — shared across all utility functions
# -------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "project.log"  # single file for all logs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# This logger will be used by all functions in utils.py
logger = logging.getLogger("pc_project")

# -------------------------------------------------------------------
# Example function 1: clean_data
# -------------------------------------------------------------------
def clean_data(data, date_cols, text_cols, num_cols):
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
                .str.strip()
                .str.lower()
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

    logger.info("Data cleaning complete.")
    logger.info(f"Output shape: {df.shape}")
    logger.info("-" * 50)
    return df