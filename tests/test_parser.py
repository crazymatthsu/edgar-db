"""Tests for the Company Facts JSON parser."""

from edgar_db.parser import parse_company_facts


class TestParseCompanyFacts:
    def test_extracts_revenue(self, sample_facts_json: dict) -> None:
        rows = parse_company_facts(320193, sample_facts_json)
        revenue_rows = [r for r in rows if r.canonical_name == "revenue"]
        assert len(revenue_rows) >= 2
        # Should have FY2022 and FY2023 annual + Q2 quarterly
        annual = [r for r in revenue_rows if r.form == "10-K"]
        assert len(annual) == 2

    def test_tag_priority_uses_first_match(self, sample_facts_json: dict) -> None:
        """Revenue should come from 'Revenues' tag (first in priority), not
        'RevenueFromContractWithCustomerExcludingAssessedTax'."""
        rows = parse_company_facts(320193, sample_facts_json)
        revenue_rows = [r for r in rows if r.canonical_name == "revenue" and r.form == "10-K"]
        # All revenue rows should use the 'Revenues' tag since it was first and had data
        for r in revenue_rows:
            assert r.tag == "Revenues"

    def test_dedup_by_period(self, sample_facts_json: dict) -> None:
        """Same metric+period+fp+form should not produce duplicate rows."""
        rows = parse_company_facts(320193, sample_facts_json)
        keys = set()
        for r in rows:
            key = (r.canonical_name, r.period_end, r.fiscal_period, r.form)
            assert key not in keys, f"Duplicate: {key}"
            keys.add(key)

    def test_filters_valid_forms_only(self, sample_facts_json: dict) -> None:
        rows = parse_company_facts(320193, sample_facts_json)
        for r in rows:
            assert r.form in ("10-K", "10-Q")

    def test_extracts_multiple_statements(self, sample_facts_json: dict) -> None:
        rows = parse_company_facts(320193, sample_facts_json)
        statements = {r.statement for r in rows}
        assert "income" in statements
        assert "balance" in statements
        assert "cashflow" in statements

    def test_eps_uses_usd_per_shares_unit(self, sample_facts_json: dict) -> None:
        rows = parse_company_facts(320193, sample_facts_json)
        eps_rows = [r for r in rows if r.canonical_name == "eps_basic"]
        assert len(eps_rows) > 0
        for r in eps_rows:
            assert r.unit == "USD/shares"

    def test_correct_values(self, sample_facts_json: dict) -> None:
        rows = parse_company_facts(320193, sample_facts_json)
        rev_2023 = [
            r for r in rows
            if r.canonical_name == "revenue" and r.fiscal_year == 2023 and r.form == "10-K"
        ]
        assert len(rev_2023) == 1
        assert rev_2023[0].value == 383285000000

    def test_empty_facts(self) -> None:
        rows = parse_company_facts(1, {"facts": {"us-gaap": {}}})
        assert rows == []

    def test_no_us_gaap(self) -> None:
        rows = parse_company_facts(1, {"facts": {}})
        assert rows == []
