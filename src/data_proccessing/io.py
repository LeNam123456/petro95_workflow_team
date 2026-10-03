"""File I/O utilities for the SPAFS V5.2 data pipeline.

Provides thin, safety-checked wrappers around pandas read/write
operations. Every function:

* Coerces ``str`` paths to ``pathlib.Path`` to prevent AttributeError.
* Creates parent directories automatically before writing.
* Logs each write operation for reproducibility auditing.

Supported formats:
* **CSV** — read and write (``index=False``).
* **Parquet** — write via the PyArrow engine (``index=False``).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("SPAFS_V5.2")


def read_csv(path: Path | str, **kwargs) -> pd.DataFrame:
    """Read a CSV file into a DataFrame with an existence guard.

    Args:
        path: Absolute or relative path to the CSV file.
        **kwargs: Forwarded verbatim to ``pd.read_csv``.

    Returns:
        pd.DataFrame: The parsed CSV contents.

    Raises:
        FileNotFoundError: If *path* does not exist on disk.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    logger.debug("Reading CSV: %s", path)
    return pd.read_csv(path, **kwargs)


def write_parquet(
    df: pd.DataFrame,
    path: Path | str,
    **kwargs,
) -> None:
    """Write a DataFrame to a Parquet file (PyArrow, no index).

    Parent directories are created if they do not exist.

    Args:
        df: DataFrame to persist.
        path: Destination file path.
        **kwargs: Forwarded verbatim to ``df.to_parquet``.

    Returns:
        None
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow", **kwargs)
    logger.info("Wrote parquet: %s  (%d rows)", path.name, len(df))


def write_csv(
    df: pd.DataFrame,
    path: Path | str,
    **kwargs,
) -> None:
    """Write a DataFrame to a CSV file (no index).

    Parent directories are created if they do not exist.

    Args:
        df: DataFrame to persist.
        path: Destination file path.
        **kwargs: Forwarded verbatim to ``df.to_csv``.

    Returns:
        None
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, **kwargs)
    logger.info("Wrote CSV: %s  (%d rows)", path.name, len(df))