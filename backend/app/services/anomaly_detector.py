"""CSV import anomaly detection pipeline.

Each anomaly type has its own detection function. All 14 anomaly types
from the prompt are implemented as separate, composable rules.

Detection functions take a list of parsed CSV rows (dicts) and group context,
returning a list of anomaly records.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


# --------------------------------------------------------------------------
# Anomaly type constants
# --------------------------------------------------------------------------
ANOMALY_TYPES = [
    "DUPLICATE_ENTRY",
    "SETTLEMENT_AS_EXPENSE",
    "CURRENCY_MISMATCH",
    "NEGATIVE_AMOUNT",
    "MEMBER_NOT_IN_GROUP",
    "DATE_OUT_OF_MEMBERSHIP",
    "MISSING_REQUIRED_FIELD",
    "SPLIT_DOES_NOT_SUM",
    "INCONSISTENT_DUPLICATE",
    "INVALID_DATE_FORMAT",
    "ZERO_AMOUNT",
    "FUTURE_DATE",
    "UNKNOWN_SPLIT_TYPE",
    "ORPHAN_SPLIT",
]

# Settlement keyword patterns
SETTLEMENT_KEYWORDS = re.compile(
    r"\b(settlement|settled|paid.*back|returned|reimbursed|repaid|payback)\b",
    re.IGNORECASE,
)

# Common date formats to try parsing
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
]

VALID_SPLIT_TYPES = {"equal", "exact", "percentage", "shares"}


def _parse_amount(raw: str | None) -> tuple[Decimal | None, str | None]:
    """
    Parse an amount string, handling currency symbols.
    Returns (amount, detected_currency_symbol).
    """
    if raw is None or str(raw).strip() == "":
        return None, None

    raw_str = str(raw).strip()
    detected_currency = None

    # Detect currency symbols
    if "$" in raw_str or "USD" in raw_str.upper():
        detected_currency = "USD"
    elif "€" in raw_str or "EUR" in raw_str.upper():
        detected_currency = "EUR"
    elif "₹" in raw_str or "INR" in raw_str.upper():
        detected_currency = "INR"

    # Clean the string for numeric parsing
    cleaned = re.sub(r"[₹$€,\s]", "", raw_str)
    cleaned = re.sub(r"(?i)(USD|INR|EUR)", "", cleaned).strip()

    try:
        return Decimal(cleaned), detected_currency
    except InvalidOperation:
        return None, detected_currency


def _parse_date(raw: str | None) -> date | None:
    """Try parsing a date string with multiple format patterns."""
    if raw is None or str(raw).strip() == "":
        return None

    raw_str = str(raw).strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw_str, fmt).date()
        except ValueError:
            continue

    return None


def _make_anomaly(
    row_number: int, raw_row: dict, anomaly_type: str,
    description: str, suggested_action: str,
) -> dict:
    """Helper to create a standardized anomaly dict."""
    return {
        "row_number": row_number,
        "raw_row": raw_row,
        "anomaly_type": anomaly_type,
        "description": description,
        "suggested_action": suggested_action,
        "user_decision": "pending",
    }


# --------------------------------------------------------------------------
# 1. DUPLICATE_ENTRY — Same description + date + amount appears twice
# --------------------------------------------------------------------------
def descriptions_match_fuzzy(d1: str, d2: str) -> bool:
    """Check if two descriptions match fuzzily."""
    d1_clean = d1.strip().lower()
    d2_clean = d2.strip().lower()
    if d1_clean == d2_clean:
        return True
    
    # Check Levenshtein distance
    dist = levenshtein_distance(d1_clean, d2_clean)
    if dist <= 2:
        return True
        
    # Check if they share a significant keyword of length >= 5
    words1 = set(w for w in re.split(r'\W+', d1_clean) if len(w) >= 5)
    words2 = set(w for w in re.split(r'\W+', d2_clean) if len(w) >= 5)
    common = words1.intersection(words2)
    generic = {"dinner", "lunch", "order", "groceries", "office", "weekly", "monthly", "shared", "shared_expenses", "apartment", "salary"}
    significant_common = common - generic
    if significant_common:
        return True
        
    return False


def detect_duplicate_entry(rows: list[dict]) -> list[dict]:
    """Flag rows where date, amount, and description (fuzzy) match another row."""
    anomalies = []
    seen_rows = []

    for row in rows:
        desc = str(row.get("description", "")).strip()
        date_str = str(row.get("date", "")).strip()
        amount_str = str(row.get("amount", "")).strip()
        
        # Check if we have seen a matching row before
        duplicate_of = None
        for prev in seen_rows:
            if (prev["date"] == date_str and 
                prev["amount"] == amount_str and 
                descriptions_match_fuzzy(prev["desc"], desc)):
                duplicate_of = prev
                break
                
        if duplicate_of:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "DUPLICATE_ENTRY",
                f"Duplicate of row {duplicate_of['row_number']}: same date '{date_str}', "
                f"amount '{amount_str}' and similar description '{desc}'",
                f"Suggest keeping row {duplicate_of['row_number']} and deleting this row. Approve deletion?",
            ))
        else:
            seen_rows.append({
                "row_number": row["_row_number"],
                "desc": desc,
                "date": date_str,
                "amount": amount_str
            })

    return anomalies


# --------------------------------------------------------------------------
# 2. SETTLEMENT_AS_EXPENSE — Description contains settlement keywords
# --------------------------------------------------------------------------
def detect_settlement_as_expense(rows: list[dict]) -> list[dict]:
    """Flag rows whose description suggests a settlement, not an expense."""
    anomalies = []
    for row in rows:
        desc = str(row.get("description", ""))
        if SETTLEMENT_KEYWORDS.search(desc):
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "SETTLEMENT_AS_EXPENSE",
                f"Description '{desc}' suggests this is a settlement/payment, not an expense.",
                "Suggest converting to a Settlement record instead of an expense. Approve conversion?",
            ))
    return anomalies


# --------------------------------------------------------------------------
# 3. CURRENCY_MISMATCH — Amount has $ or USD but currency field says INR
# --------------------------------------------------------------------------
def detect_currency_mismatch(rows: list[dict]) -> list[dict]:
    """Flag rows where the amount field contains currency symbols that don't match the currency column,
    or where the currency field is missing/empty."""
    anomalies = []
    for row in rows:
        amount_str = str(row.get("amount", ""))
        currency_field = str(row.get("currency", "")).strip().upper()

        # Flag missing currency field
        if not currency_field:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "CURRENCY_MISMATCH",
                f"Currency field is empty. Cannot determine if amount '{amount_str}' "
                f"is in INR, USD, or another currency.",
                "Suggest defaulting to INR. Please confirm the correct currency.",
            ))
            continue

        _, detected = _parse_amount(amount_str)

        if detected and detected != currency_field:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "CURRENCY_MISMATCH",
                f"Amount '{amount_str}' contains {detected} symbol but currency field "
                f"says '{currency_field}'.",
                f"Suggest updating currency to '{detected}'. Please confirm the exchange rate.",
            ))
    return anomalies


# --------------------------------------------------------------------------
# 4. NEGATIVE_AMOUNT — Amount < 0
# --------------------------------------------------------------------------
def detect_negative_amount(rows: list[dict]) -> list[dict]:
    """Flag rows where the amount is negative (treated as refund)."""
    anomalies = []
    for row in rows:
        amount, _ = _parse_amount(str(row.get("amount", "")))
        if amount is not None and amount < 0:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "NEGATIVE_AMOUNT",
                f"Amount {amount} is negative. This will be treated as a refund.",
                "Suggest flipping sign to positive and recording as a credit/refund. Approve?",
            ))
    return anomalies


# --------------------------------------------------------------------------
# 5. MEMBER_NOT_IN_GROUP — paid_by or split mentions unknown name
# --------------------------------------------------------------------------
def detect_member_not_in_group(
    rows: list[dict], member_names: list[str]
) -> list[dict]:
    """
    Flag rows where paid_by or split_with references a name not in the group.
    Uses fuzzy matching (Levenshtein ≤ 2) to suggest corrections.
    """
    anomalies = []
    member_names_lower = [n.lower() for n in member_names]

    def _check_name(name: str, row: dict) -> dict | None:
        """Check a single name against known members, return anomaly or None."""
        name = name.strip()
        if not name:
            return None
        if name.lower() in member_names_lower:
            return None

        # Try fuzzy matching
        best_match = None
        best_distance = float("inf")
        for known in member_names:
            dist = levenshtein_distance(name.lower(), known.lower())
            if dist < best_distance:
                best_distance = dist
                best_match = known

        if best_distance <= 2 and best_match:
            return _make_anomaly(
                row["_row_number"], row,
                "MEMBER_NOT_IN_GROUP",
                f"'{name}' is not a group member. "
                f"Did you mean '{best_match}'? (Levenshtein distance: {best_distance})",
                f"Suggest mapping '{name}' → '{best_match}'. Approve fix?",
            )
        else:
            return _make_anomaly(
                row["_row_number"], row,
                "MEMBER_NOT_IN_GROUP",
                f"'{name}' is not a group member and no close match found.",
                "Cannot auto-fix. Please manually assign a member or skip this row.",
            )

    for row in rows:
        # Check paid_by
        paid_by = str(row.get("paid_by", "")).strip()
        if paid_by:
            anomaly = _check_name(paid_by, row)
            if anomaly:
                anomalies.append(anomaly)

        # Check split_with names
        split_members = str(row.get("split_with") or row.get("split_among") or "")
        if split_members:
            for name in split_members.split(";"):
                name = name.strip()
                if name:
                    anomaly = _check_name(name, row)
                    if anomaly:
                        anomalies.append(anomaly)

    return anomalies


# --------------------------------------------------------------------------
# 6. DATE_OUT_OF_MEMBERSHIP — Expense date outside member's window
# --------------------------------------------------------------------------
def detect_date_out_of_membership(
    rows: list[dict],
    member_windows: dict[str, tuple[date, date | None]],
) -> list[dict]:
    """
    Flag rows where the expense date falls outside a member's active window.

    member_windows: { member_name: (joined_at, left_at_or_None) }
    """
    anomalies = []
    for row in rows:
        expense_date = _parse_date(str(row.get("date", "")))
        if expense_date is None:
            continue

        paid_by = str(row.get("paid_by", "")).strip()

        for member_name, (joined, left) in member_windows.items():
            # Check if this member is mentioned in splits or is the payer
            split_members = str(row.get("split_with") or row.get("split_among") or "").lower()
            is_involved = (
                member_name.lower() == paid_by.lower()
                or member_name.lower() in split_members
            )

            if is_involved:
                if expense_date < joined:
                    anomalies.append(_make_anomaly(
                        row["_row_number"], row,
                        "DATE_OUT_OF_MEMBERSHIP",
                        f"{member_name} joined on {joined} but expense is dated {expense_date}. "
                        f"They weren't a member yet.",
                        f"Suggest excluding {member_name} from the split and redistributing equally.",
                    ))
                elif left is not None and expense_date >= left:
                    anomalies.append(_make_anomaly(
                        row["_row_number"], row,
                        "DATE_OUT_OF_MEMBERSHIP",
                        f"{member_name} left on {left} but expense is dated {expense_date}. "
                        f"They were no longer a member.",
                        f"Suggest excluding {member_name} from the split and redistributing equally.",
                    ))

    return anomalies


# --------------------------------------------------------------------------
# 7. MISSING_REQUIRED_FIELD — date, amount, paid_by, or description is empty
# --------------------------------------------------------------------------
def detect_missing_required_field(rows: list[dict]) -> list[dict]:
    """Flag rows missing required fields: date, amount, paid_by, description."""
    required = ["date", "amount", "paid_by", "description"]
    anomalies = []

    for row in rows:
        missing = [
            f for f in required
            if not str(row.get(f, "")).strip()
        ]
        if missing:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "MISSING_REQUIRED_FIELD",
                f"Missing required field(s): {', '.join(missing)}. Row cannot be imported as-is.",
                "Row is non-importable. Please provide values manually or skip this row.",
            ))

    return anomalies


# --------------------------------------------------------------------------
# 8. SPLIT_DOES_NOT_SUM — Percentages ≠ 100 or exact amounts ≠ total
# --------------------------------------------------------------------------
def _parse_split_details(split_data: str, is_percentage: bool) -> list[Decimal] | None:
    """
    Parse split_details in CSV format like:
      - "Aisha 30%; Rohan 30%; Priya 30%; Meera 20%" (percentage)
      - "Rohan 700; Priya 400; Meera 400" (exact/unequal)
      - "Aisha 1; Rohan 2; Priya 1; Dev 2" (shares)
    Also handles simple comma-separated values: "40,40,20"
    Returns list of Decimal values, or None if unparseable.
    """
    if not split_data or not str(split_data).strip():
        return None

    raw = str(split_data).strip()
    values = []

    if ";" in raw:
        # Semicolon-separated "Name Value[%]" format
        for part in raw.split(";"):
            part = part.strip()
            if not part:
                continue
            if is_percentage:
                match = re.search(r'(\d+(?:\.\d+)?)\s*%', part)
            else:
                match = re.search(r'(\d+(?:\.\d+)?)\s*$', part)
            if match:
                try:
                    values.append(Decimal(match.group(1)))
                except InvalidOperation:
                    return None
    else:
        # Comma-separated plain numbers
        for part in raw.split(","):
            part = part.strip().rstrip("%")
            if part:
                try:
                    values.append(Decimal(part))
                except InvalidOperation:
                    return None

    return values if values else None


def detect_split_does_not_sum(rows: list[dict]) -> list[dict]:
    """Flag rows where split values don't add up correctly."""
    anomalies = []

    for row in rows:
        split_type = str(row.get("split_type", "equal")).strip().lower()

        # Use split_details (CSV column) or split_values as fallback
        split_data = row.get("split_details", "") or row.get("split_values", "")

        if split_type == "percentage":
            values = _parse_split_details(split_data, is_percentage=True)
            if values:
                total_pct = sum(values)
                if total_pct != Decimal("100"):
                    anomalies.append(_make_anomaly(
                        row["_row_number"], row,
                        "SPLIT_DOES_NOT_SUM",
                        f"Percentages sum to {total_pct}%, not 100%. "
                        f"Discrepancy: {Decimal('100') - total_pct}%",
                        "Suggest auto-adjusting the largest share to make it balance. Approve?",
                    ))

        elif split_type in ("exact", "unequal"):
            amount, _ = _parse_amount(str(row.get("amount", "")))
            values = _parse_split_details(split_data, is_percentage=False)
            if values and amount:
                total_shares = sum(values)
                if total_shares != amount:
                    anomalies.append(_make_anomaly(
                        row["_row_number"], row,
                        "SPLIT_DOES_NOT_SUM",
                        f"Exact split amounts sum to {total_shares} but total is {amount}. "
                        f"Discrepancy: {amount - total_shares}",
                        "Suggest auto-adjusting the largest share to make it balance. Approve?",
                    ))

    return anomalies


# --------------------------------------------------------------------------
# 9. INCONSISTENT_DUPLICATE — Same event, different amounts
# --------------------------------------------------------------------------
def detect_inconsistent_duplicate(rows: list[dict]) -> list[dict]:
    """Flag rows where the same date and fuzzy description appear with different amounts."""
    anomalies = []
    
    # Group rows by date
    by_date: dict[str, list[dict]] = {}
    for row in rows:
        dt = str(row.get("date", "")).strip()
        if dt:
            if dt not in by_date:
                by_date[dt] = []
            by_date[dt].append(row)
            
    for dt, day_rows in by_date.items():
        # Compare every pair of rows on this day
        for i in range(len(day_rows)):
            for j in range(i + 1, len(day_rows)):
                r1 = day_rows[i]
                r2 = day_rows[j]
                
                desc1 = str(r1.get("description", "")).strip()
                desc2 = str(r2.get("description", "")).strip()
                
                amount1 = str(r1.get("amount", "")).strip()
                amount2 = str(r2.get("amount", "")).strip()
                
                # If they have different amounts but similar description, they are inconsistent
                if amount1 != amount2 and descriptions_match_fuzzy(desc1, desc2):
                    anomalies.append(_make_anomaly(
                        r2["_row_number"], r2,
                        "INCONSISTENT_DUPLICATE",
                        f"Same event similar to '{desc1}' on {dt} logged with different amounts: "
                        f"{amount1} vs {amount2}",
                        "Review both entries side by side and pick the correct value, or enter a new one.",
                    ))
                    
    return anomalies


# --------------------------------------------------------------------------
# 10. INVALID_DATE_FORMAT — Date not parseable
# --------------------------------------------------------------------------
def detect_invalid_date_format(rows: list[dict]) -> list[dict]:
    """Flag rows with unparseable date values."""
    anomalies = []
    for row in rows:
        raw_date = str(row.get("date", "")).strip()
        if raw_date and _parse_date(raw_date) is None:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "INVALID_DATE_FORMAT",
                f"Cannot parse date '{raw_date}'. Tried formats: "
                f"YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY, and others.",
                "Please provide the date in YYYY-MM-DD format.",
            ))
    return anomalies


# --------------------------------------------------------------------------
# 11. ZERO_AMOUNT — Amount is 0
# --------------------------------------------------------------------------
def detect_zero_amount(rows: list[dict]) -> list[dict]:
    """Flag rows with zero amount (likely placeholder)."""
    anomalies = []
    for row in rows:
        amount, _ = _parse_amount(str(row.get("amount", "")))
        if amount is not None and amount == 0:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "ZERO_AMOUNT",
                "Amount is 0 — this is likely a placeholder row.",
                "Suggest skipping this row. It will not be imported.",
            ))
    return anomalies


# --------------------------------------------------------------------------
# 12. FUTURE_DATE — Expense date in the future
# --------------------------------------------------------------------------
def detect_future_date(rows: list[dict]) -> list[dict]:
    """Flag rows with dates in the future (warn only, still import)."""
    today = date.today()
    anomalies = []

    for row in rows:
        expense_date = _parse_date(str(row.get("date", "")))
        if expense_date is not None and expense_date > today:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "FUTURE_DATE",
                f"Expense date {expense_date} is in the future (today is {today}). "
                f"This could be a planned expense.",
                "Warning only — this row will still be imported unless you choose to skip.",
            ))

    return anomalies


# --------------------------------------------------------------------------
# 13. UNKNOWN_SPLIT_TYPE — split_type not in known enum
# --------------------------------------------------------------------------
def detect_unknown_split_type(rows: list[dict]) -> list[dict]:
    """Flag rows with unrecognized split types."""
    anomalies = []
    for row in rows:
        split_type = str(row.get("split_type", "")).strip().lower()
        if split_type and split_type not in VALID_SPLIT_TYPES:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "UNKNOWN_SPLIT_TYPE",
                f"Split type '{split_type}' is not recognized. "
                f"Valid types: {', '.join(sorted(VALID_SPLIT_TYPES))}.",
                "Suggest defaulting to 'equal' split. Approve?",
            ))
    return anomalies


# --------------------------------------------------------------------------
# 14. ORPHAN_SPLIT — Split references a non-existent expense
# --------------------------------------------------------------------------
def detect_orphan_split(
    rows: list[dict], existing_expense_ids: set[str]
) -> list[dict]:
    """Flag split entries that reference an expense_id that doesn't exist."""
    anomalies = []
    for row in rows:
        expense_ref = str(row.get("expense_id", "")).strip()
        if expense_ref and expense_ref not in existing_expense_ids:
            anomalies.append(_make_anomaly(
                row["_row_number"], row,
                "ORPHAN_SPLIT",
                f"Split references expense_id '{expense_ref}' which does not exist.",
                "This split has no parent expense. Suggest deleting. Approve?",
            ))
    return anomalies


# --------------------------------------------------------------------------
# Pipeline orchestrator
# --------------------------------------------------------------------------
def run_anomaly_pipeline(
    rows: list[dict],
    member_names: list[str],
    member_windows: dict[str, tuple[date, date | None]],
    existing_expense_ids: set[str] | None = None,
) -> list[dict]:
    """
    Run all 14 anomaly detection rules against a set of parsed CSV rows.

    Returns a combined list of all detected anomalies, sorted by row number.
    """
    if existing_expense_ids is None:
        existing_expense_ids = set()

    all_anomalies = []

    # Run each detector
    all_anomalies.extend(detect_duplicate_entry(rows))
    all_anomalies.extend(detect_settlement_as_expense(rows))
    all_anomalies.extend(detect_currency_mismatch(rows))
    all_anomalies.extend(detect_negative_amount(rows))
    all_anomalies.extend(detect_member_not_in_group(rows, member_names))
    all_anomalies.extend(detect_date_out_of_membership(rows, member_windows))
    all_anomalies.extend(detect_missing_required_field(rows))
    all_anomalies.extend(detect_split_does_not_sum(rows))
    all_anomalies.extend(detect_inconsistent_duplicate(rows))
    all_anomalies.extend(detect_invalid_date_format(rows))
    all_anomalies.extend(detect_zero_amount(rows))
    all_anomalies.extend(detect_future_date(rows))
    all_anomalies.extend(detect_unknown_split_type(rows))
    all_anomalies.extend(detect_orphan_split(rows, existing_expense_ids))

    # Sort by row number for consistent presentation
    all_anomalies.sort(key=lambda a: a["row_number"])

    return all_anomalies
