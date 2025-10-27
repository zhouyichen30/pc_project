# streamlit_app.py
import sys
import subprocess
from pathlib import Path
import streamlit as st

#This Streamlit dashboard provides an interactive interface for the Private Credit Performance pipeline.
#It allows users to apply a custom parallel shocks to the monthly interest rate data, trigger the underlying data-processing workflow, and visualize the resulting Gross vs. Net IRR chart on different levels.


REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
OUTPUTS = REPO_ROOT / "outputs"
PLOT = OUTPUTS / "irr_plot.png"

st.set_page_config(page_title="Private Credit IRR Runner", layout="centered")
st.title("Private Credit Performance")

st.write(
    "Note: The applied shock is a **parallel shift** that adds the specified value "
    "to all monthly interest rates in the curve (e.g., 0.01 = +100 bps). "
    "It is applied only at the **fund level**, impacting **net IRR** and **net MOIC** results. "
    "For full model details, see: https://github.com/zhouyichen30/pc_project?tab=readme-ov-file"
)

st.write(
    "Enter an optional interest-rate shock (absolute decimal). "
    "Examples: 0.01 = +100 bps, -0.0025 = –25 bps."
)

shock = st.number_input(
    "Shock (decimal)", value=0.0, step=0.0025, format="%.5f", help="Leave 0.0 for no shock"
)

run = st.button("Run pipeline")

def run_pipeline(shock_value: float):
    """
    Try running from repo root (works if package is editable-installed).
    If that fails, fall back to running from src/ (your current README flow).
    """
    base_cmd = [sys.executable, "-m", "irr_calc"]
    if shock_value != 0.0:
        base_cmd += ["--shock", f"{shock_value}"]

    # Attempt from REPO_ROOT first
    proc = subprocess.run(base_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        # Fallback: run from src/
        proc = subprocess.run(base_cmd, cwd=str(SRC_DIR), capture_output=True, text=True)
    return proc

if run:
    st.info("Running pipeline… this will execute `python -m irr_calc`.")
    result = run_pipeline(shock)

    st.subheader("Chart")
    if PLOT.exists():
        st.image(str(PLOT), caption=str(PLOT.relative_to(REPO_ROOT)))
        with PLOT.open("rb") as f:
            st.download_button("Download irr_plot.png", data=f, file_name="irr_plot.png")
    else:
        st.warning(f"Chart not found at {PLOT}. Check logs/output paths.")
