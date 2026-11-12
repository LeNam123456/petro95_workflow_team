"""Split loading and dataset access routines.

Ensures physical partitions are accessed read-only and checksum-verified.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.data.validation import verify_splits_integrity


def load_physical_splits(
    splits_dir: str | Path = "data/splits",
    manifest_path: str | Path | None = None,
    verify_checksums: bool = True,
) -> dict[str, pd.DataFrame]:
    """Load Train, Validation, and Test partitions from disk in read-only mode."""
    s_dir = Path(splits_dir)
    m_path = Path(manifest_path) if manifest_path is not None else s_dir / "splits_manifest.json"

    if verify_checksums and m_path.exists():
        verify_splits_integrity(m_path, raise_on_error=True)

    train_df = pd.read_parquet(s_dir / "train_2008_2020.parquet")
    val_df = pd.read_parquet(s_dir / "val_2021_2023.parquet")
    test_df = pd.read_parquet(s_dir / "test_2024_2025.parquet")

    return {
        "train": train_df,
        "val": val_df,
        "test": test_df,
    }
