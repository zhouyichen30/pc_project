import pandas as pd
import logging

logger = logging.getLogger("pc_project")

def merge_deal_level(level_3_metrics_db: pd.DataFrame,
                     level_2_metrics_db: pd.DataFrame,
                     level_1_metrics_db: pd.DataFrame) -> pd.DataFrame:
    """
    Merge metrics across facility (level 3), deal (level 2), and fund (level 1).

    Each DataFrame should contain:
      ['fund', 'deal_id', 'entity_id', 'paid_in', 'distr', 'MOIC', 'xirr']

    The function prefixes columns by level for clarity and merges hierarchically.
    """
    # Prefix metric columns for clarity
    level_3_prefixed = level_3_metrics_db.rename(
        columns={c: f"facility_level_{c}" for c in ['paid_in', 'distr', 'MOIC', 'xirr']}
    )

    level_2_prefixed = level_2_metrics_db.rename(
        columns={c: f"deal_level_{c}" for c in ['paid_in', 'distr', 'MOIC', 'xirr']}
    )

    level_1_prefixed = level_1_metrics_db.rename(
        columns={c: f"fund_level_{c}" for c in ['paid_in', 'distr', 'MOIC', 'xirr']}
    )

    # Merge hierarchically
    merged = pd.merge(level_3_prefixed, level_2_prefixed, on=['deal_id', 'fund'], how='left')
    merged = pd.merge(merged, level_1_prefixed, on='fund', how='left')

    logger.info(f"Merged all levels — final shape: {merged.shape}")
    return merged
