"""Shared matplotlib helpers.

The backend renders charts headlessly, so the Agg backend is selected before
pyplot is imported. Doing it in one place keeps every chart module
consistent.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def save_and_close(fig, path: str, **kwargs) -> None:
    """Save a figure and close it, so pyplot does not accumulate open figures.

    ``plt.close()`` is needed, not just ``plt.clf()``, otherwise the figure
    stays registered with pyplot and memory grows with every upload.
    """
    fig.tight_layout()
    fig.savefig(path, **kwargs)
    plt.close(fig)


def plot_bar(counts: pd.Series, title: str, path: str) -> None:
    """Write a bar chart of ``counts`` to ``path``."""
    fig, ax = plt.subplots()
    counts.plot(kind="bar", ax=ax)
    ax.set_title(title)
    save_and_close(fig, path)
