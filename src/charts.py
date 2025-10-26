import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def plot_irr_highlighted(df: pd.DataFrame,OUT_path: str) -> None:
    """
    Plot gross and net IRR for each Facility, Deal, and Fund,
    with black rectangle highlights per level and percent labels on bars.

    Parameters
    ----------
    df : pd.DataFrame
        Must include columns:
        ['level', 'name', 'gross_irr', 'net_irr'].
        net_irr may contain 'N/A' strings.

    Returns
    -------
    None
        Displays a single chart (no file output).
        Save it in output folder
    """
    logger.info("plot_irr_highlighted: starting chart build.")

    # Prepare data
    df = df.copy()
    df['gross_irr'] = pd.to_numeric(df['gross_irr'], errors='coerce')
    df['net_irr'] = (
        df['net_irr']
        .replace('N/A', np.nan)
        .infer_objects(copy=False)
        .pipe(pd.to_numeric, errors='coerce')
    )

    # Keep rows with at least one IRR value
    df = df.dropna(subset=['gross_irr', 'net_irr'], how='all')
    if df.empty:
        logger.warning("plot_irr_highlighted: no valid IRR data to plot. Exiting.")
        return

    # Enforce visual order and sort
    order = pd.CategoricalDtype(['Facility', 'Deal', 'Fund'], ordered=True)
    df['level'] = df['level'].astype(order)
    df = df.sort_values(['level', 'name']).reset_index(drop=True)

    # Log counts per level
    counts = df['level'].value_counts(dropna=False).to_dict()
    logger.info("plot_irr_highlighted: counts by level %s", counts)

    # Bars
    x = np.arange(len(df))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, df['gross_irr'], width, label='Gross IRR')
    bars2 = ax.bar(x + width/2, df['net_irr'],   width, label='Net IRR')

    # Labels on bars (percentage, 2 decimals)
    for bars in (bars1, bars2):
        for b in bars:
            h = b.get_height()
            if not np.isnan(h):
                ax.text(
                    b.get_x() + b.get_width()/2, h,
                    f"{h*100:.2f}%",
                    ha='center', va='bottom', fontsize=8
                )

    # Axes styling
    ax.set_xticks(x)
    ax.set_xticklabels(df['name'], rotation=45, ha='right')
    ax.set_ylabel('IRR (decimal)')
    ax.set_title('Gross vs Net IRR — Highlighted by Level')
    ax.legend()
    plt.tight_layout()

    # Highlight sections by level using bar positions
    y_min, y_max = ax.get_ylim()
    for lvl in ['Facility', 'Deal', 'Fund']:
        pos = np.where(df['level'].values == lvl)[0]
        if pos.size == 0:
            continue
        start, end = pos.min(), pos.max()
        rect = plt.Rectangle(
            (start - 0.5, y_min),
            (end - start + 1),
            (y_max - y_min),
            linewidth=1.5, edgecolor='black', facecolor='none', linestyle='--'
        )
        ax.add_patch(rect)
        ax.text(
            (start + end) / 2, y_max * 0.98, lvl,
            ha='center', va='top', fontsize=10,
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2')
        )

    logger.info("plot_irr_highlighted: rendering chart to screen.")
    #save the chart to folder
    plt.savefig(OUT_path / "irr_plot.png", dpi=300, bbox_inches='tight')
    logger.info(f"Chart saved to: {OUT_path / 'irr_plot.png'}")

    #plt.show()
    #logger.info("plot_irr_highlighted: done.")
    
