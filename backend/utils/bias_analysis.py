import logging

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from utils.plotting import save_and_close

logger = logging.getLogger(__name__)


def run_bias_analysis(df: pd.DataFrame, target: str, out_dir: str) -> list[str]:
    # CLASS DISTRIBUTION
    fig, ax = plt.subplots()
    df[target].value_counts().plot(kind="bar", ax=ax)
    ax.set_title(f"Class Distribution for {target}")
    save_and_close(fig, f"{out_dir}/class_distribution.png")

    # CORRELATION MATRIX
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] > 1:
        corr = numeric_df.corr()
        fig_size = max(12, numeric_df.shape[1] * 0.5)
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))
        sns.heatmap(
            corr,
            annot=numeric_df.shape[1] <= 15,  # only annotate if small enough
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1, vmax=1,
            linewidths=0.3,
            square=True,
            ax=ax,
        )
        ax.set_title("Correlation Matrix")
        save_and_close(fig, f"{out_dir}/correlation_matrix.png", dpi=150)

    # DETECT SENSITIVE FEATURES
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    sensitive_cols = [c for c in cat_cols if df[c].nunique() <= 10 and c != target]

    report = []
    report.append(f"Dataset Shape: {df.shape}")
    report.append(f"Target Column: {target}")
    report.append("\nClass Distribution:\n" + str(df[target].value_counts()))

    # BIAS REPORTS
    for col in sensitive_cols:
        group_counts = df.groupby([col, target]).size().unstack(fill_value=0)
        report.append(f"\nBias Analysis for {col}:\n{group_counts}")

        fig, ax = plt.subplots()
        group_counts.plot(kind="bar", ax=ax)
        ax.set_title(f"{col} vs {target}")
        save_and_close(fig, f"{out_dir}/sensitive_{col}_bias.png")

    with open(f"{out_dir}/bias_report.txt", "w") as f:
        f.write("\n\n".join(report))

    logger.info("Bias analysis completed. Sensitive columns detected: %s", sensitive_cols)
    return sensitive_cols
