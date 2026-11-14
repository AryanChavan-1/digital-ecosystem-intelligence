import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from app.core.errors import AmbiguousDateFormatException

# Null/empty representation tokens
NULL_TOKENS = {
    "",
    "-",
    "--",
    "---",
    "n/a",
    "na",
    "null",
    "none",
    "nil",
    "#n/a",
    "#value!",
    "nan",
}

# Regex to detect summary/footer rows
SUMMARY_ROW_PATTERN = re.compile(
    r"^(total|grand\s+total|sub\s+total|subtotal|average|summary)\b",
    re.IGNORECASE,
)

# Currency and percentage symbols/prefixes to strip
CURRENCY_PREFIX_PATTERN = re.compile(
    r"^(₹|rs\.?|inr|\$|usd|€|eur|£|gbp)\s*",
    re.IGNORECASE,
)
CURRENCY_SUFFIX_PATTERN = re.compile(
    r"\s*(₹|rs\.?|inr|\$|usd|€|eur|£|gbp|%)$",
    re.IGNORECASE,
)


def clean_string(val: Any) -> Optional[str]:
    """
    Trim string and return None if empty or null-like token.
    Never fabricate '0' for missing fields.
    """
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in NULL_TOKENS:
        return None
    return s


def clean_monetary(val: Any) -> Optional[Decimal]:
    """
    Clean monetary / numeric values strictly as Decimal (never float).
    Strips Indian currency symbols (₹, INR, Rs.), commas (including Indian lakhs/crores: 1,00,000),
    and percentage symbols.
    Returns None for missing/null-like strings.
    """
    cleaned = clean_string(val)
    if cleaned is None:
        return None

    # Strip currency prefixes and suffixes
    cleaned = CURRENCY_PREFIX_PATTERN.sub("", cleaned).strip()
    cleaned = CURRENCY_SUFFIX_PATTERN.sub("", cleaned).strip()

    # Strip percentage signs and trailing/leading whitespace
    cleaned = cleaned.rstrip("%").strip()

    # Remove commas (handles both Western 100,000 and Indian 1,00,000)
    cleaned = cleaned.replace(",", "").strip()

    if not cleaned or cleaned.lower() in NULL_TOKENS:
        return None

    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        # In case of remaining non-numeric chars
        num_match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if num_match:
            try:
                return Decimal(num_match.group(0))
            except InvalidOperation:
                return None
        return None


def clean_integer(val: Any) -> Optional[int]:
    """
    Clean integer values (impressions, clicks).
    Strips commas, symbols, and parses strictly via Decimal to int.
    Returns None for missing/null-like fields.
    """
    dec = clean_monetary(val)
    if dec is None:
        return None
    return int(dec)


def is_summary_row_text(val: Any) -> bool:
    """Check if a cell value indicates a summary / footer row."""
    if val is None:
        return False
    s = str(val).strip()
    return bool(SUMMARY_ROW_PATTERN.match(s))


def is_summary_row(row_dict_or_list: Any, check_keys: Optional[List[str]] = None) -> bool:
    """
    Check if a row starts with or contains a summary keyword in campaign/date or first cells.
    """
    if isinstance(row_dict_or_list, dict):
        # Check specific mapped keys if provided
        if check_keys:
            for k in check_keys:
                if k in row_dict_or_list and is_summary_row_text(row_dict_or_list[k]):
                    return True
        # Check all values in dict
        for v in row_dict_or_list.values():
            if is_summary_row_text(v):
                return True
        return False
    elif isinstance(row_dict_or_list, (list, tuple)):
        for item in row_dict_or_list:
            if is_summary_row_text(item):
                return True
        return False
    return is_summary_row_text(row_dict_or_list)


def normalize_date_format_string(fmt: Optional[str]) -> Optional[str]:
    """Translate user-friendly format hints like 'DD/MM/YYYY' into Python strptime format."""
    if not fmt:
        return None
    clean_fmt = fmt.strip()
    mapping = {
        "DD/MM/YYYY": "%d/%m/%Y",
        "DD-MM-YYYY": "%d-%m-%Y",
        "MM/DD/YYYY": "%m/%d/%Y",
        "MM-DD-YYYY": "%m-%d-%Y",
        "YYYY-MM-DD": "%Y-%m-%d",
        "YYYY/MM/DD": "%Y/%m/%d",
    }
    return mapping.get(clean_fmt.upper(), clean_fmt)


def resolve_date_format(
    sample_dates: List[str],
    explicit_format: Optional[str] = None,
) -> str:
    """
    Deterministic Date Ambiguity Resolver:
    1. If explicit_format is provided, normalize and return it.
    2. If all sample dates match YYYY-MM-DD (or ISO), return '%Y-%m-%d'.
    3. If dates use delimiters (/ or -) with 4-digit year at end:
       - If any sample has part1 > 12 and part2 <= 12 -> Unambiguously DD/MM/YYYY ('%d/%m/%Y').
       - If any sample has part2 > 12 and part1 <= 12 -> Unambiguously MM/DD/YYYY ('%m/%d/%Y').
       - If ALL sample dates have part1 <= 12 and part2 <= 12 -> Genuinely ambiguous!
         Raise AmbiguousDateFormatException prompting user for format.
    """
    if explicit_format:
        return normalize_date_format_string(explicit_format) or explicit_format

    # Filter out empty or null strings
    valid_samples = [s.strip() for s in sample_dates if clean_string(s)]
    if not valid_samples:
        return "%Y-%m-%d"

    # Check if all match ISO YYYY-MM-DD
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    if all(iso_pattern.match(s) for s in valid_samples):
        return "%Y-%m-%d"

    # Inspect delimiter-separated dates (e.g. DD/MM/YYYY or MM/DD/YYYY)
    delim_pattern = re.compile(r"^(\d{1,2})([/\-\.])(\d{1,2})([/\-\.])(\d{2,4})")

    day_first_evidence = False
    month_first_evidence = False
    separator = "/"
    has_delimited = False

    for s in valid_samples:
        m = delim_pattern.match(s)
        if m:
            has_delimited = True
            p1 = int(m.group(1))
            sep = m.group(2)
            p2 = int(m.group(3))
            separator = sep

            if p1 > 12 and p2 <= 12:
                day_first_evidence = True
            elif p2 > 12 and p1 <= 12:
                month_first_evidence = True

    if has_delimited:
        if day_first_evidence and not month_first_evidence:
            return f"%d{separator}%m{separator}%Y"
        elif month_first_evidence and not day_first_evidence:
            return f"%m{separator}%d{separator}%Y"
        elif not day_first_evidence and not month_first_evidence:
            # Genuinely ambiguous: every sample has both day and month <= 12
            raise AmbiguousDateFormatException(
                details={
                    "sample_values": valid_samples[:5],
                    "options": ["DD/MM/YYYY", "MM/DD/YYYY"],
                }
            )

    # Fallback to ISO
    return "%Y-%m-%d"


def parse_date_to_local_date(
    date_val: Any,
    date_format: str,
    timezone_str: str = "Asia/Kolkata",
) -> date:
    """
    Parse a date string/datetime into a datetime.date respecting workspace timezone.
    Default timezone is Asia/Kolkata.
    """
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val

    if isinstance(date_val, datetime):
        if date_val.tzinfo is None:
            # Treat as UTC or target timezone
            tz = ZoneInfo(timezone_str)
            return date_val.replace(tzinfo=tz).date()
        else:
            return date_val.astimezone(ZoneInfo(timezone_str)).date()

    cleaned = clean_string(date_val)
    if not cleaned:
        raise ValueError("Cannot parse empty date string")

    # If ISO datetime with T and timezone offset or Z
    if "T" in cleaned:
        try:
            # Handle ISO string with fromisoformat
            iso_str = cleaned.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo:
                return dt.astimezone(ZoneInfo(timezone_str)).date()
            return dt.date()
        except ValueError:
            pass

    # Try explicit format
    try:
        dt = datetime.strptime(cleaned, date_format)
        return dt.date()
    except ValueError:
        pass

    # Fallbacks for common formats
    for fallback in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(cleaned, fallback).date()
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date '{date_val}' with format '{date_format}'")


def sanitize_csv_records(
    csv_content: str | bytes | io.StringIO,
    mapping: Dict[str, str],
    date_format_hint: Optional[str] = None,
    timezone_str: str = "Asia/Kolkata",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Sanitize CSV data using specified column mapping:
    Mapping dictionary maps canonical fields -> CSV header names:
      - 'date': header for local_date
      - 'campaign_name': header for campaign name
      - 'channel': header for channel (optional)
      - 'currency': header for currency (optional, default INR)
      - 'impressions': header for impressions
      - 'clicks': header for clicks
      - 'spend': header for spend
      - 'conversions': header for conversions
      - 'attributed_revenue': header for attributed revenue
      - 'creative_label': header (optional)
      - 'audience_label': header (optional)

    Returns (valid_rows, dropped_or_quarantined_rows).
    """
    if isinstance(csv_content, bytes):
        text = csv_content.decode("utf-8-sig", errors="replace")
        stream = io.StringIO(text)
    elif isinstance(csv_content, str):
        stream = io.StringIO(csv_content)
    else:
        stream = csv_content

    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        return [], []

    raw_rows = list(reader)

    # 1. Filter out summary/footer rows
    data_rows: List[Dict[str, str]] = []
    dropped_summary_rows: List[Dict[str, Any]] = []

    date_col = mapping.get("date")
    campaign_col = mapping.get("campaign_name")
    check_cols = [c for c in [date_col, campaign_col] if c]

    for idx, row in enumerate(raw_rows):
        if is_summary_row(row, check_keys=check_cols):
            dropped_summary_rows.append({"row_number": idx + 2, "raw": row, "reason": "summary_row"})
        else:
            data_rows.append(row)

    if not data_rows:
        return [], dropped_summary_rows

    # 2. Inspect sample dates for ambiguity resolution
    sample_dates: List[str] = []
    if date_col:
        for r in data_rows:
            raw_date = r.get(date_col)
            if raw_date and clean_string(raw_date):
                sample_dates.append(raw_date)

    resolved_format = resolve_date_format(sample_dates, explicit_format=date_format_hint)

    # 3. Parse and sanitize rows
    valid_rows: List[Dict[str, Any]] = []
    quarantined_rows: List[Dict[str, Any]] = list(dropped_summary_rows)

    for idx, row in enumerate(data_rows):
        try:
            # Parse date
            raw_date_str = row.get(date_col) if date_col else None
            if not raw_date_str or not clean_string(raw_date_str):
                quarantined_rows.append({
                    "row_number": idx + 2,
                    "reason": "missing_required_date",
                    "raw": row,
                })
                continue

            local_d = parse_date_to_local_date(
                raw_date_str, resolved_format, timezone_str=timezone_str
            )

            # Campaign name
            camp_name = clean_string(row.get(campaign_col)) if campaign_col else "Default Campaign"
            if not camp_name:
                camp_name = "Unnamed Campaign"

            # Channel & Currency
            channel = clean_string(row.get(mapping.get("channel", ""))) if "channel" in mapping else None
            currency = clean_string(row.get(mapping.get("currency", ""))) if "currency" in mapping else None
            if not currency:
                currency = "INR"

            # Metrics
            impressions = clean_integer(row.get(mapping.get("impressions", ""))) if "impressions" in mapping else 0
            clicks = clean_integer(row.get(mapping.get("clicks", ""))) if "clicks" in mapping else 0
            spend = clean_monetary(row.get(mapping.get("spend", ""))) if "spend" in mapping else Decimal("0.0000")
            conversions = clean_monetary(row.get(mapping.get("conversions", ""))) if "conversions" in mapping else Decimal("0.0000")
            rev = clean_monetary(row.get(mapping.get("attributed_revenue", ""))) if "attributed_revenue" in mapping else Decimal("0.0000")

            creative_label = clean_string(row.get(mapping.get("creative_label", ""))) if "creative_label" in mapping else None
            audience_label = clean_string(row.get(mapping.get("audience_label", ""))) if "audience_label" in mapping else None

            valid_rows.append({
                "local_date": local_d,
                "campaign_name": camp_name,
                "channel": channel,
                "currency": currency.upper() if currency else "INR",
                "impressions": impressions or 0,
                "clicks": clicks or 0,
                "spend": spend if spend is not None else Decimal("0.0000"),
                "conversions": conversions if conversions is not None else Decimal("0.0000"),
                "attributed_revenue": rev if rev is not None else Decimal("0.0000"),
                "creative_label": creative_label,
                "audience_label": audience_label,
            })
        except Exception as e:
            quarantined_rows.append({
                "row_number": idx + 2,
                "reason": f"parsing_error: {str(e)}",
                "raw": row,
            })

    return valid_rows, quarantined_rows
