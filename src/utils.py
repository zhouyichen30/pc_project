import pandas as pd

def clean_data(data,date_cols,text_cols,num_cols):
    """"
    This funcation clean any data_frame and output a cleaned dataframe that has correct for each categray
    data: the data
    date_cols: the name of the columns in data in a list, this fucnation will convert them
    text_cols: the name of..
    num_cols: the name of...
    """
    # 1. Convert date columns
    for col in date_cols:
        data[col] = pd.to_datetime(data[col], errors='coerce')

    # 2. Clean text columns (strip whitespace, unify casing)
    for col in text_cols:
        data[col] = (
            data[col]
            .astype(str)             # ensure string type
            .str.strip()             # remove leading/trailing spaces
            .str.lower()             # optional: make lowercase for consistency
        )

    # 3. Convert numeric columns
    for col in num_cols:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    return data