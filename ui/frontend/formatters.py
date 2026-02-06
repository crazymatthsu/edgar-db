"""Number formatting and metric label helpers."""

from __future__ import annotations


def format_number(value: float | None) -> str:
    """Format large numbers with B/M/K suffixes."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}${abs_val / 1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{sign}${abs_val / 1e9:.2f}B"
    if abs_val >= 1e6:
        return f"{sign}${abs_val / 1e6:.2f}M"
    if abs_val >= 1e3:
        return f"{sign}${abs_val / 1e3:.2f}K"
    return f"{sign}${abs_val:,.2f}"


def humanize_metric(metric: str) -> str:
    """Convert snake_case metric name to a human-readable label."""
    replacements = {
        "eps": "EPS",
        "sga": "SG&A",
    }
    words = metric.split("_")
    result = []
    for word in words:
        if word in replacements:
            result.append(replacements[word])
        else:
            result.append(word.capitalize())
    return " ".join(result)
