from datetime import date
from decimal import Decimal

import pytest

from app.core.errors import AmbiguousDateFormatException
from app.services.locale_parser import (
    clean_integer,
    clean_monetary,
    clean_string,
    is_summary_row,
    parse_date_to_local_date,
    resolve_date_format,
    sanitize_csv_records,
)


def test_clean_string():
    assert clean_string("  hello world  ") == "hello world"
    assert clean_string("") is None
    assert clean_string("   ") is None
    assert clean_string("--") is None
    assert clean_string("-") is None
    assert clean_string("N/A") is None
    assert clean_string("NA") is None
    assert clean_string("null") is None
    assert clean_string("None") is None


def test_clean_monetary_indian_currency_and_lakhs():
    # Indian rupee symbol and lakhs formatting
    assert clean_monetary("₹1,24,500.50") == Decimal("124500.50")
    assert clean_monetary("Rs. 1,00,000") == Decimal("100000")
    assert clean_monetary("Rs 50,000.25") == Decimal("50000.25")
    assert clean_monetary("INR 10,00,000.00") == Decimal("1000000.00")

    # Percentage
    assert clean_monetary("2.45%") == Decimal("2.45")
    assert clean_monetary("0.05%") == Decimal("0.05")

    # Null / missing representations
    assert clean_monetary("--") is None
    assert clean_monetary("-") is None
    assert clean_monetary("N/A") is None
    assert clean_monetary("") is None
    assert clean_monetary("   ") is None

    # Western commas and USD
    assert clean_monetary("$12,345.67") == Decimal("12345.67")
    assert clean_monetary("USD 500") == Decimal("500")


def test_clean_integer():
    assert clean_integer("1,24,500") == 124500
    assert clean_integer("₹50,000") == 50000
    assert clean_integer("--") is None
    assert clean_integer("N/A") is None
    assert clean_integer("") is None


def test_is_summary_row():
    assert is_summary_row({"Campaign": "Total", "Date": "2026-05-15"}) is True
    assert is_summary_row({"Campaign": "Grand Total", "Date": "2026-05-15"}) is True
    assert is_summary_row({"Campaign": "Sub Total", "Date": "2026-05-15"}) is True
    assert is_summary_row({"Campaign": "Average", "Date": "2026-05-15"}) is True
    assert is_summary_row({"Campaign": "Total Results"}) is True
    assert is_summary_row(["Average", "100", "200"]) is True

    # Regular rows
    assert is_summary_row({"Campaign": "Summer Brand Awareness", "Date": "2026-05-15"}) is False
    assert is_summary_row(["2026-05-15", "Brand Push", "5000"]) is False


def test_resolve_date_format_unambiguous():
    # Day > 12 -> unambiguous DD/MM/YYYY
    samples_dmy = ["15/05/2026", "24/05/2026", "08/05/2026"]
    assert resolve_date_format(samples_dmy) == "%d/%m/%Y"

    # Month first with Day > 12 -> unambiguous MM/DD/YYYY
    samples_mdy = ["05/15/2026", "05/24/2026", "05/08/2026"]
    assert resolve_date_format(samples_mdy) == "%m/%d/%Y"

    # ISO format YYYY-MM-DD
    samples_iso = ["2026-05-15", "2026-05-16"]
    assert resolve_date_format(samples_iso) == "%Y-%m-%d"


def test_resolve_date_format_ambiguous_raises():
    # Both day and month <= 12 across all rows
    ambiguous_samples = ["04/05/2026", "01/02/2026", "11/12/2026"]

    with pytest.raises(AmbiguousDateFormatException) as exc_info:
        resolve_date_format(ambiguous_samples)

    assert exc_info.value.code == "AMBIGUOUS_DATE_FORMAT"
    assert "sample_values" in exc_info.value.details


def test_resolve_date_format_with_explicit_hint():
    # Ambiguous sample with explicit user hint should NOT raise
    ambiguous_samples = ["04/05/2026", "01/02/2026"]
    res = resolve_date_format(ambiguous_samples, explicit_format="DD/MM/YYYY")
    assert res == "%d/%m/%Y"

    res_mdy = resolve_date_format(ambiguous_samples, explicit_format="MM/DD/YYYY")
    assert res_mdy == "%m/%d/%Y"


def test_parse_date_to_local_date_timezone_normalization():
    # Standard date string
    parsed = parse_date_to_local_date("2026-05-15", "%Y-%m-%d", timezone_str="Asia/Kolkata")
    assert parsed == date(2026, 5, 15)

    # DD/MM/YYYY format
    parsed_dmy = parse_date_to_local_date("15/05/2026", "%d/%m/%Y", timezone_str="Asia/Kolkata")
    assert parsed_dmy == date(2026, 5, 15)

    # ISO string with UTC timezone edge: 2026-05-14T22:30:00Z -> IST is 2026-05-15 04:00:00 (+5:30)
    parsed_utc = parse_date_to_local_date(
        "2026-05-14T22:30:00Z", "%Y-%m-%d", timezone_str="Asia/Kolkata"
    )
    assert parsed_utc == date(2026, 5, 15)


def test_sanitize_csv_records_full_lifecycle():
    csv_data = """Day,Campaign Name,Platform,Currency,Impressions,Clicks,Amount Spent (INR),Purchases,Purchase Conversion Value,CTR
15/05/2026,"Summer D2C Launch",Meta,INR,"1,24,500","3,450","₹1,24,500.50","120","₹3,73,501.50","2.77%"
16/05/2026,"Summer D2C Launch",Meta,INR,"85,000","2,100","₹75,000.00","--","₹1,50,000.00","2.47%"
Total,"Total Results",Meta,INR,"2,09,500","5,550","₹1,99,500.50","120","₹5,23,501.50","2.65%"
"""
    mapping = {
        "date": "Day",
        "campaign_name": "Campaign Name",
        "channel": "Platform",
        "currency": "Currency",
        "impressions": "Impressions",
        "clicks": "Clicks",
        "spend": "Amount Spent (INR)",
        "conversions": "Purchases",
        "attributed_revenue": "Purchase Conversion Value",
    }

    valid_rows, quarantined = sanitize_csv_records(csv_data, mapping=mapping)

    # 1. Total row must be dropped as summary row
    assert len(valid_rows) == 2
    assert any(q.get("reason") == "summary_row" for q in quarantined)

    # 2. Row 1 check
    r1 = valid_rows[0]
    assert r1["local_date"] == date(2026, 5, 15)
    assert r1["campaign_name"] == "Summer D2C Launch"
    assert r1["channel"] == "Meta"
    assert r1["currency"] == "INR"
    assert r1["impressions"] == 124500
    assert r1["clicks"] == 3450
    assert r1["spend"] == Decimal("124500.50")
    assert r1["conversions"] == Decimal("120")
    assert r1["attributed_revenue"] == Decimal("373501.50")

    # 3. Row 2 check: purchases was '--', cleanly converted without fabricating numbers
    r2 = valid_rows[1]
    assert r2["local_date"] == date(2026, 5, 16)
    assert r2["conversions"] == Decimal("0.0000")
    assert r2["spend"] == Decimal("75000.00")
