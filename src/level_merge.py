import pandas as pd
import logging

logger = logging.getLogger("pc_project")

def merge_deal_level(l3, l2, l1):
    """
    Combine and standardize Facility-, Deal-, and Fund-level performance metrics.

    This function vertically stacks all three data levels in order:
    Facility → Deal → Fund.
    The order is important to ensure lower-level data appears first for
    IRR aggregation or waterfall-style calculations.

    Parameters
    ----------
    l3 : pd.DataFrame
        Facility-level metrics. Must include:
        ['entity_id', 'deal_id', 'fund', 'paid_in', 'distr' or 'distributed', 'MOIC', 'xirr']
    l2 : pd.DataFrame
        Deal-level metrics. Must include:
        ['deal_id', 'fund', 'paid_in', 'distr' or 'distributed', 'MOIC', 'xirr']
    l1 : pd.DataFrame
        Fund-level metrics. Must include:
        ['fund', 'paid_in', 'distr' or 'distributed', 'MOIC', 'xirr']

    Returns
    -------
    pd.DataFrame
        A single stacked DataFrame with the following columns:
        ['level', 'id', 'name', 'paid_in', 'distributed',
         'gross_irr', 'gross_moic', 'net_irr', 'net_moic']

        - 'level' marks whether the row is Facility, Deal, or Fund.
        - 'id' corresponds to the entity/deal/fund identifier.
        - 'name' carries the fund name (Fund level only).
        - 'gross_irr' and 'gross_moic' mirror the input xirr/MOIC (net metrics).
        - 'net_irr' and 'net_moic' are left blank for now.

    Notes
    -----
    The function converts numeric fields safely and logs:
      • total row count
      • per-level counts
      • missing value summary
    """
    # Standardize and label each level
    l3_ = l3.rename(columns={'distr': 'distributed'}).assign(level='Facility', id=l3['entity_id'], name=l3['facility_name'])
    l2_ = l2.rename(columns={'distr': 'distributed'}).assign(level='Deal',     id=l2['deal_id'],   name=l2['deal_name'])
    l1_ = l1.rename(columns={'distr': 'distributed'}).assign(level='Fund',     id=l1['fund'],      name=l1['fund'])

    # Stack all levels (lower → higher)
    df = pd.concat([l3_, l2_, l1_], ignore_index=True)

    # Convert numeric and map columns
    for c in ['paid_in', 'distributed', 'MOIC', 'xirr']:
        df[c] = pd.to_numeric(df.get(c), errors='coerce')

    df['gross_irr'] = df['xirr']
    df['gross_moic'] = df['MOIC']
    df['net_irr'] = pd.NA
    df['net_moic'] = pd.NA

    out = df[['level', 'id', 'name', 'paid_in', 'distributed',
              'gross_irr', 'gross_moic', 'net_irr', 'net_moic']]

    # Simple logging
    logger.info(f"Merged all levels — total rows: {len(out)}")
    logger.info(f"Facility: {len(l3_)}, Deal: {len(l2_)}, Fund: {len(l1_)}")

    na_summary = out.isna().sum().to_dict()
    logger.info(f"Missing values summary: {na_summary}")

    return out

def assign_fund_net_metrics(mdc_cleanned: pd.DataFrame,
                            level_1_metrics_db_net: pd.DataFrame) -> pd.DataFrame:
    """
    Assign fund-level net IRR and net MOIC from level_1_metrics_db_net
    back to the corresponding fund rows in mdc_cleanned.

    Parameters
    ----------
    mdc_cleanned : pd.DataFrame
        Dataset containing all levels (Facility, Deal, Fund) with columns:
        ['level', 'fund', 'net_irr', 'net_moic', ...].
    level_1_metrics_db_net : pd.DataFrame
        Fund-level dataset with columns:
        ['fund', 'xirr', 'MOIC'].

    Returns
    -------
    pd.DataFrame
        Updated mdc_cleanned where fund-level rows have
        'net_irr' and 'net_moic' values populated from level_1_metrics_db_net.
    """
    df = mdc_cleanned.merge(
        level_1_metrics_db_net[['fund', 'xirr', 'MOIC']],
        left_on='id',
        right_on='fund',
        how='left',
        suffixes=('', '_fund')
    )

    # assign fund-level net IRR and MOIC
    df.loc[df['level'] == 'Fund', 'net_irr'] = df['xirr']
    df.loc[df['level'] == 'Fund', 'net_moic'] = df['MOIC']

    # drop helper columns
    df = df.drop(columns=['xirr', 'MOIC','fund'])
    # fill missing values
    df = df.fillna('N/A')

    # logging
    logger.info(
        "assign_fund_net_metrics: updated fund-level net_irr and net_moic for %d funds."
    )

    return df