from __future__ import annotations

from secmaster_db.parser import (
    build_security_row,
    classify_style_box,
    parse_openfigi_response,
    parse_yfinance_info,
)


def test_classify_style_box_large() -> None:
    assert classify_style_box(10_000_000_000) == "large_cap"
    assert classify_style_box(50_000_000_000) == "large_cap"


def test_classify_style_box_mid() -> None:
    assert classify_style_box(2_000_000_000) == "mid_cap"
    assert classify_style_box(9_999_999_999) == "mid_cap"


def test_classify_style_box_small() -> None:
    assert classify_style_box(1_999_999_999) == "small_cap"
    assert classify_style_box(0) == "small_cap"


def test_parse_yfinance_info() -> None:
    info = {
        "longName": "Apple Inc.",
        "isin": "US0378331005",
        "sharesOutstanding": 15_000_000_000,
        "country": "United States",
        "currency": "USD",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3_000_000_000_000,
    }
    result = parse_yfinance_info("AAPL", info)
    assert result["name"] == "Apple Inc."
    assert result["isin"] == "US0378331005"
    assert result["shares_outstanding"] == 15_000_000_000
    assert result["country"] == "United States"
    assert result["exchange_currency"] == "USD"
    assert result["sector"] == "Technology"
    assert result["market_cap"] == 3_000_000_000_000.0


def test_parse_yfinance_info_missing_fields() -> None:
    info = {"shortName": "AAPL"}
    result = parse_yfinance_info("AAPL", info)
    assert result["name"] == "AAPL"
    assert result["isin"] == ""
    assert result["shares_outstanding"] == 0
    assert result["market_cap"] == 0.0


def test_parse_openfigi_response() -> None:
    data = {
        "figi": "BBG000B9XRY4",
        "shareClassFIGI": "BBG001S5N8V8",
        "micCode": "XNAS",
        "securityType": "Common Stock",
    }
    result = parse_openfigi_response(data)
    assert result["figi"] == "BBG000B9XRY4"
    assert result["share_class_figi"] == "BBG001S5N8V8"
    assert result["exchange_mic"] == "XNAS"


def test_parse_openfigi_response_missing() -> None:
    result = parse_openfigi_response({})
    assert result["figi"] == ""
    assert result["share_class_figi"] == ""
    assert result["exchange_mic"] == ""


def test_build_security_row_with_figi() -> None:
    yf_data = {
        "name": "Apple Inc.",
        "isin": "US0378331005",
        "shares_outstanding": 15_000_000_000,
        "country": "United States",
        "exchange_currency": "USD",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3_000_000_000_000.0,
    }
    figi_data = {
        "figi": "BBG000B9XRY4",
        "shareClassFIGI": "BBG001S5N8V8",
        "micCode": "XNAS",
    }
    sec = build_security_row("aapl", yf_data, figi_data, "2024-01-01T00:00:00")
    assert sec.ticker == "AAPL"
    assert sec.name == "Apple Inc."
    assert sec.figi == "BBG000B9XRY4"
    assert sec.exchange_mic == "XNAS"
    assert sec.style_box == "large_cap"


def test_build_security_row_without_figi() -> None:
    yf_data = {
        "name": "Small Co",
        "isin": "",
        "shares_outstanding": 1_000_000,
        "country": "US",
        "exchange_currency": "USD",
        "sector": "Healthcare",
        "industry": "Biotech",
        "market_cap": 500_000_000.0,
    }
    sec = build_security_row("SMCO", yf_data, None, "2024-01-01T00:00:00")
    assert sec.ticker == "SMCO"
    assert sec.figi == ""
    assert sec.style_box == "small_cap"
