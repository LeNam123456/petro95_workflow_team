"""Visualization utilities for forecasting benchmark results."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def plot_loss_curves(
    loss_histories: dict[str, dict[str, list[float]]],
    output_path: str | Path,
) -> None:
    """Plot training and validation loss curves across recurrent model configurations.

    Parameters:
    - loss_histories: Mapping of config_label -> {"train": [losses], "val": [losses]}
    - output_path: Destination path for saved PNG figure.
    """
    if not loss_histories:
        return

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    n_configs = len(loss_histories)
    cols = 3
    rows = (n_configs + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(15, 3.5 * rows), squeeze=False)
    axes_flat = axes.flatten()

    for idx, (label, history) in enumerate(loss_histories.items()):
        ax = axes_flat[idx]
        train_loss = history.get("train", [])
        val_loss = history.get("val", [])
        epochs = list(range(1, max(len(train_loss), len(val_loss)) + 1))

        if train_loss:
            ax.plot(epochs[:len(train_loss)], train_loss, label="Train Loss", color="royalblue", alpha=0.8)
        if val_loss:
            ax.plot(epochs[:len(val_loss)], val_loss, label="Val Loss", color="crimson", alpha=0.8)

        ax.set_title(label, fontsize=10, fontweight="bold")
        ax.set_xlabel("Epoch", fontsize=8)
        ax.set_ylabel("MSE Loss", fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=8)

    # Hide any unused subplots
    for j in range(idx + 1, len(axes_flat)):
        fig.delaxes(axes_flat[j])

    fig.tight_layout()
    fig.savefig(out_file, dpi=150)
    plt.close(fig)
