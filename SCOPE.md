# Scope & Specifications

## 1. Database Schema
The database uses PostgreSQL with the following core entities and constraints:
- `users`: Stores user identity, bcrypt `password_hash`, and emails.
- `groups`: Container for flatmates, tracks `base_currency`.
- `group_members`: Time-bound membership via `joined_at` and nullable `left_at` (null = currently active).
- `expenses`: Stores original currency values, `amount_in_inr` conversion, and `is_deleted` for soft deletes.
- `expense_splits`: Granular division per user including `raw_share_units` and `share_amount_inr`.
- `settlements`: Distinct table tracking real-world payments from one user to another.
- `import_sessions` & `import_anomalies`: Tracks stateful batch CSV imports without immediate mutation.
- `audit_log`: Centralized immutable ledger capturing all INSERT/UPDATE/DELETE actions.

## 2. Membership Logic
A member is strictly liable for an expense **only if** the expense date falls within their active membership window.
The calculation is defined as: `joined_at <= expense.date < left_at`. 
(If `left_at` is NULL, the member is considered active indefinitely).

For instance, Meera left at the end of March. She will not be included in April's splits. Sam joined mid-April, so he is excluded from early April splits. If an anomaly or user attempts to assign them a share outside their window, their share is reduced to 0 and the remaining members equally absorb the cost.

## 3. CSV Anomaly Detection Policies
The CSV pipeline uses 14 strictly defined anomaly detectors that run sequentially without mutating the actual data:

1. **DUPLICATE_ENTRY:** (Identical amount, date, description) Flags both rows. Keeps the first, asks user to approve deletion of the second.
2. **SETTLEMENT_AS_EXPENSE:** Flags descriptions containing "settlement", "paid back". Suggests converting row to a Settlement record.
3. **CURRENCY_MISMATCH:** Flags rows with $ or USD text if base is INR. Extracts amount, requests exchange rate confirmation.
4. **NEGATIVE_AMOUNT:** Treats amount < 0 as a refund. Flips sign to positive, creates a credit balance split.
5. **MEMBER_NOT_IN_GROUP:** Uses Levenshtein distance (fuzzy match). If distance ≤ 2, suggests mapping. Otherwise, flags as unknown.
6. **DATE_OUT_OF_MEMBERSHIP:** (Sam/Meera rule). Flags that the member is removed from the split for this expense.
7. **MISSING_REQUIRED_FIELD:** Halts import of the row if date, amount, paid_by, or description is missing.
8. **SPLIT_DOES_NOT_SUM:** Mathematical check. Discrepancy is shown. Auto-adjusts the largest share by the remaining pennies to balance it.
9. **INCONSISTENT_DUPLICATE:** Similar description/date but different amount. Suggests review.
10. **INVALID_DATE_FORMAT:** Attempts strict parsing (DD/MM/YYYY, MM-DD-YYYY). Flags if unparseable.
11. **ZERO_AMOUNT:** Skips entirely with an internal note.
12. **FUTURE_DATE:** Emits a warning but allows import.
13. **UNKNOWN_SPLIT_TYPE:** Checks against `equal`, `exact`, `percentage`, `shares`. Flags if invalid.
14. **ORPHAN_SPLIT:** Ensures no splits exist without a matching master expense record.
