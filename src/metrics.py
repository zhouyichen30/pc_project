import pandas as pd
import logging
from scipy.optimize import newton


logger = logging.getLogger("pc_project")


def _pic_calc(level: str, mdb: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Paid-In Capital (PIC) for a given grouping level.

    Parameters
    ----------
    level : str
        Column name or list of columns to group by 
        (e.g., 'facility_id', 'deal_id', 'fund', or ['entity_id', 'deal_id', 'fund']).
    mdb : pd.DataFrame
        Dataset containing at least ['amount', level].

    Returns
    -------
    pd.DataFrame
        DataFrame with columns [level, 'paid_in'].
        'paid_in' remains negative to reflect cash outflows.
    """
    df = mdb.copy()

    if 'amount' not in df.columns:
        logger.warning("Column 'amount' not found — skipping PIC calculation.")
        return pd.DataFrame()

    # Allow multiple grouping levels
    if isinstance(level, list):
        missing_cols = [col for col in level if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing grouping columns: {missing_cols}. Skipping PIC calculation.")
            return pd.DataFrame()
    elif level not in df.columns:
        logger.warning(f"Grouping level '{level}' not found — skipping PIC calculation.")
        return pd.DataFrame()

    # Filter only negative cashflows (capital contributions)
    paid_in_df = df[df['amount'] < 0]
    #I want to convert to postive for reporting purpse
    paid_in_df['amount'] = paid_in_df['amount'] * -1
     

    if paid_in_df.empty:
        logger.info(f"No negative cashflows found for level '{level}'.")
        return pd.DataFrame(columns=([level] if isinstance(level, str) else level) + ['paid_in'])

    # Group and sum
    result = (
        paid_in_df.groupby(level, as_index=False)['amount']
        .sum()
        .rename(columns={'amount': 'paid_in'})
    )

    logger.info(f"Calculated paid-in capital for {len(result)} grouped records at level {level}.")
    return result

def _dis_calc(level: str, mdb: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Distributions (sum of positive cashflows) at the given grouping level.

    Parameters
    ----------
    level : str or list[str]
        Column name or list of columns to group by 
        (e.g., 'facility_id', 'deal_id', 'fund', or ['entity_id', 'deal_id', 'fund']).
    mdb : pd.DataFrame
        Dataset containing at least ['amount', level].

    Returns
    -------
    pd.DataFrame
        DataFrame with columns [level, 'distr'].
        'distr' is positive to reflect cash inflows.
    """
    df = mdb.copy()

    if 'amount' not in df.columns:
        logger.warning("Column 'amount' not found — skipping distribution calculation.")
        return pd.DataFrame()

    # Validate grouping keys
    if isinstance(level, list):
        missing_cols = [col for col in level if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing grouping columns: {missing_cols}. Skipping distribution calculation.")
            return pd.DataFrame()
        key_cols = level
    else:
        if level not in df.columns:
            logger.warning(f"Grouping level '{level}' not found — skipping distribution calculation.")
            return pd.DataFrame()
        key_cols = [level]

    # Filter only positive cashflows (distributions/returns)
    df_pos = df[df['amount'] > 0]

    if df_pos.empty:
        logger.info(f"No positive cashflows found for level '{level}'.")
        return pd.DataFrame(columns=key_cols + ['distr'])

    # Group and sum
    result = (
        df_pos.groupby(level, as_index=False)['amount']
        .sum()
        .rename(columns={'amount': 'distr'})
    )

    logger.info(f"Calculated distributions for {len(result)} grouped records at level {level}.")
    return result


def _xnpv(rate, cashflows, dates):
    """
    Compute the Net Present Value (XNPV) for irregular cashflows.
    This function will be used as f(x) = 0 in the Newton method to solve for XIRR.

    Parameters
    ----------
    rate : float
        Discount rate (decimal form, e.g., 0.10 for 10%).
    cashflows : list or array-like
        Cashflow amounts (negative = contributions, positive = distributions).
    dates : list or array-like
        Corresponding cashflow dates.

    Returns
    -------
    float
        Net present value at the given rate.
    """
    if len(cashflows) != len(dates):
        raise ValueError("cashflows and dates must have the same length")

    t0 = min(dates)
    npv = 0.0
    for cf, d in zip(cashflows, dates):
        t = (d - t0).days / 365.0
        npv += cf / ((1 + rate) ** t)
    return npv

def xirr(cashflows, dates):
    """
    Excel-style XIRR solved via Newton on xnpv(r, cashflows, dates) = 0.

    Notes
    -----
    - Sign convention: contributions are negative; distributions are positive.
    - Day count: ACT/365 (handled inside xnpv).
    - Requires at least one negative and one positive cashflow.
    - Logs input validation and convergence results.
    """
    if len(cashflows) != len(dates):
        logger.warning("xirr(): cashflows and dates must have the same length.")
        return None

    if not (any(cf > 0 for cf in cashflows) and any(cf < 0 for cf in cashflows)):
        logger.warning("xirr(): cashflows must include at least one positive and one negative value.")
        return None

    try:
        initial_guess = -0.1 if sum(cashflows) < 0 else 0.1
        irr = newton(
            lambda r: _xnpv(r, cashflows, dates),
            x0=initial_guess,
            tol=1e-6,
            maxiter=10000,
        )
        logger.info(f"xirr(): Converged successfully at {irr:.6f}")
        return irr
    except Exception as e:
        logger.warning(f"xirr(): Newton method did not converge. Error: {e}")
        return None




def metrics(level: str, mdb: pd.DataFrame) -> pd.DataFrame:
    """
    Compute portfolio metrics at the specified grouping level.

    This function aggregates:
      - Paid-In Capital (PIC): total contributed capital (negative cashflows)
      - Distributions (DIS): total returned capital (positive cashflows)
      - MOIC: multiple on invested capital = distributions / |paid_in|
      - IRR: XIRR based on actual dated cashflows per entity

    Parameters
    ----------
    level : str or list[str]
        Column name(s) to group by (e.g., 'facility_id', 'deal_id', 'fund').
    mdb : pd.DataFrame
        Dataset containing at least ['amount', 'asof', level].

    Returns
    -------
    pd.DataFrame
        DataFrame with columns [level, paid_in, distr, MOIC, xirr].
    """
    logger.info(f"Computing metrics at level: {level}")
    #returns only Paid-In Capital (PIC)
    pic_df = _pic_calc(level, mdb)
    #returns 
    dis_df = _dis_calc(level, mdb)
    
    # Merge results on the grouping key(s)
    metrics_df = pd.merge(pic_df, dis_df, on=level, how='outer')

    # Fill missing columns with 0 in case some groups have only inflows or outflows
    metrics_df = metrics_df.fillna({'paid_in': 0, 'distr': 0})

    #moic calc
    metrics_df['MOIC'] = metrics_df['distr'] / metrics_df['paid_in']

    # IRR calc for this data model — use the first column in the level list
    irr_loop = level[0]
    logger.info(f"IRR calculation starts on the {irr_loop} level")
    rows = []
    ulist = mdb[irr_loop].dropna().unique()

    for i in ulist:
        # filter this group's cashflows and sort by date
        cdb = mdb[mdb[irr_loop] == i].sort_values('asof')
        irr_val = xirr(cdb['amount'].tolist(), cdb['asof'].tolist())
        rows.append({irr_loop: i, 'xirr': irr_val})

    irr_df = pd.DataFrame(rows)
    # now merge back with merge df
    metrics_df = pd.merge(metrics_df, irr_df, on=irr_loop, how='outer')




    logger.info(f"Metrics calculated and merged for {len(metrics_df)} {level} records.")

    return metrics_df
