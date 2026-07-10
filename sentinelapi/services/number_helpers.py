"""Helper functions for number-related operations."""


def _decimal_to_float(value):
    """Convert Decimal-like computed values into JSON-friendly numbers."""
    if value is None:
        return None

    return float(value)


def _average_decimal_values(values):
    """Average Decimal values, returning None when no values are available."""
    if not values:
        return None

    return float(round(sum(values) / len(values), 2))
