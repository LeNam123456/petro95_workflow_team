"""Custom exception hierarchy for the SPAFS V5.2 data pipeline.

Defines domain-specific exceptions that enforce strict Data Contract
gates. Every gate violation must raise one of these exceptions so that
the pipeline fails loudly rather than silently propagating bad data.
"""

from __future__ import annotations


class DataContractViolationError(Exception):
    """Raised when ingested data violates a mandatory Data Contract gate.

    Each gate (PK uniqueness, date range, missing-value pattern, positive
    prices) raises this exception with a human-readable message describing
    which contract clause was breached and how many rows are affected.
    """