import argparse
import logging

logger = logging.getLogger(__name__)

def get_shock_from_cli() -> float:
    """
    Parse an optional command-line argument for interest rate shock.

    Returns
    -------
    float
        Absolute shock in decimal (e.g., 0.01 = +100 bps).
    """
    parser = argparse.ArgumentParser(
        description="Run the pipeline with optional curve shock (absolute decimal; e.g., 0.01 = +100 bps)."
    )
    parser.add_argument(
        "--shock",
        type=float,
        default=0.0,
        help="Absolute rate shock in decimal form (e.g., 0.01 = +100 bps). Default is 0.0."
    )
    args = parser.parse_args()
    logger.info(f"CLI argument parsed — curve shock: {args.shock}")
    return args.shock
