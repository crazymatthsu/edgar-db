"""Parse SEC EDGAR Company Facts JSON into FactRow lists."""

from __future__ import annotations

from typing import Any

from .models import FactRow
from .xbrl_tags import STATEMENT_TAGS

# Forms we care about
VALID_FORMS = {"10-K", "10-Q"}


def parse_company_facts(cik: int, data: dict[str, Any]) -> list[FactRow]:
    """Parse the Company Facts JSON response into a list of FactRows.

    Uses tag priority: for each canonical metric, try tags in order.
    Only the first matching tag's data is used per metric.
    """
    facts_section = data.get("facts", {})
    us_gaap = facts_section.get("us-gaap", {})

    rows: list[FactRow] = []
    seen: set[tuple[str, str, str, str]] = set()  # dedup key

    for statement_name, metrics in STATEMENT_TAGS.items():
        for canonical_name, tag_candidates in metrics.items():
            for tag in tag_candidates:
                tag_data = us_gaap.get(tag)
                if not tag_data:
                    continue

                units = tag_data.get("units", {})
                # Pick the right unit: USD for monetary, USD/shares for per-share,
                # shares for share counts, pure for ratios
                unit_data = None
                unit_label = ""
                for unit_key in ["USD", "USD/shares", "shares", "pure"]:
                    if unit_key in units:
                        unit_data = units[unit_key]
                        unit_label = unit_key
                        break

                if not unit_data:
                    continue

                tag_had_valid_data = False
                for entry in unit_data:
                    form = entry.get("form", "")
                    if form not in VALID_FORMS:
                        continue

                    # Skip entries without end date (instant vs duration ambiguity)
                    period_end = entry.get("end")
                    if not period_end:
                        continue

                    fp = entry.get("fp", "")
                    fy = entry.get("fy")
                    if fy is None:
                        continue

                    # Dedup: same metric, period, fiscal_period, form
                    dedup_key = (canonical_name, period_end, fp, form)
                    if dedup_key in seen:
                        continue

                    val = entry.get("val")
                    if val is None:
                        continue

                    seen.add(dedup_key)
                    tag_had_valid_data = True

                    rows.append(FactRow(
                        cik=cik,
                        tag=tag,
                        canonical_name=canonical_name,
                        statement=statement_name,
                        value=float(val),
                        unit=unit_label,
                        period_end=period_end,
                        fiscal_year=int(fy),
                        fiscal_period=fp,
                        form=form,
                        filed=entry.get("filed", ""),
                        accession=entry.get("accn", ""),
                    ))

                # If we found data for this tag, stop trying alternatives
                if tag_had_valid_data:
                    break

    return rows
