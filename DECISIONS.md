# Architectural & Design Decisions

This document outlines the key decisions made while building the Shared Expenses Tracker. The goal was to build a robust, production-quality, testable, and correct backend system accompanied by a dynamic modern frontend.

## 1. Tech Stack
- **Backend:** Python + FastAPI + SQLAlchemy + PostgreSQL. Chosen for strong typing, asynchronous capabilities, robust ORM, and enterprise-grade relational database guarantees.
- **Frontend:** React + TypeScript + Vite + TailwindCSS. Provides a fast development environment, type safety, and the ability to build a highly interactive, glassmorphism-styled UI quickly.
- **Deployment:** Docker & Docker Compose to ensure reproducible and isolated environments across dev and production.

## 2. Core Architecture
A strict **layered architecture** was enforced to separate concerns:
1. **Routers (`app/routers/`):** Handle HTTP requests, parsing, auth dependency injection, and HTTP responses. No complex business logic.
2. **Services (`app/services/`):** Pure Python modules handling the core domain logic (e.g., `balance_engine.py`, `split_calculator.py`, `anomaly_detector.py`). Easily unit-testable without database mocks where possible.
3. **Data Access (`app/models/` & `app/database.py`):** SQLAlchemy ORM models representing the database schema.
4. **Schemas (`app/schemas/`):** Pydantic models for strict I/O validation and serialization.

## 3. Financial Accuracy & The `Decimal` Type
**Decision:** All financial calculations use Python's `Decimal` type.
**Reason:** Floating-point arithmetic introduces precision errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). Using `Decimal` guarantees exact representation of currency.
- We quantize all final stored amounts to 2 decimal places (`Decimal("0.01")`).

## 4. Handling Indivisible Splits (The "Penny Problem")
**Problem:** Splitting ₹100 equally among 3 people mathematically yields 33.333...
**Decision:** In `split_calculator.py`, we calculate the base share (amount // members) and then distribute the remainder penny-by-penny (0.01) to the first few members until the remainder is exhausted. This guarantees that the sum of parts *exactly* equals the total amount.

## 5. Minimum-Transaction Settlement Algorithm
**Problem:** A group with many cross-debts can have a chaotic web of owe/owed relationships.
**Decision:** Implemented a greedy algorithm in `balance_engine.py`.
- Calculate net balance for every user (Total Owed - Total Owes).
- Separate users into "Debtors" (negative balance) and "Creditors" (positive balance).
- Sort both lists by magnitude (largest first).
- Greedily match the largest debtor with the largest creditor, creating a settlement.
- Repeat until all balances are zero. This significantly reduces the total number of physical transfers needed to settle the group.

## 6. The "Sam & Meera" Problem (Membership Windows)
**Problem:** Users shouldn't be involved in expenses that occurred before they joined or after they left.
**Decision:** `GroupMember` model stores `joined_at` and `left_at` (nullable).
- Defined a strict rule: A member is active on a date `D` if `joined_at <= D < left_at`. (Left date is exclusive, as the person left on that day and is no longer liable).
- The `is_active_on` method on the `GroupMember` model encapsulates this logic.

## 7. Audit Trail (Tracking the "Who")
**Problem:** We need to log who created, updated, or soft-deleted an expense, but SQLAlchemy lifecycle events (`after_insert`, `after_update`) don't naturally have access to the current HTTP request or user.
**Decision:** Used Python's `contextvars.ContextVar`.
- The FastAPI dependency `get_current_user` sets `current_audit_user_id.set(user.id)`.
- The SQLAlchemy event listeners in `app/utils/audit.py` read this ContextVar to capture the actor's ID without passing the user object explicitly through every layer of the app. This creates a clean, transparent audit trail.

## 8. CSV Import & Anomaly Detection
**Problem:** Bulk importing CSVs often leads to dirty data (duplicate rows, typos, missing data).
**Decision:** Built an isolated import session flow.
- The CSV is parsed into JSON and analyzed by `anomaly_detector.py` against 14 specific rules (including fuzzy string matching using Levenshtein distance for misspelled names).
- The import is halted, placing the session in a "reviewing" state.
- The user resolves anomalies one-by-one via the UI (`approve_fix`, `approve_delete`).
- Once all are resolved, the `finalize` endpoint runs in a single database transaction, ensuring atomicity (all or nothing).

## 9. Currency Handling ("Dollar is not a Rupee")
**Context:** Users can log expenses in foreign currencies, but balances must be calculated in a common base currency (INR).
**Decision:** Every expense stores `total_amount` (in the original currency), `currency` (e.g., "USD"), `exchange_rate_to_inr` (user-provided at time of expense), and `amount_in_inr`. All internal ledger math and debt calculations are performed strictly on `amount_in_inr`.
**Reason:** Separating the original currency from the ledger calculation ensures balances don't fluctuate unexpectedly over time as global exchange rates change.

## 10. Soft Deletes
**Context:** Users make mistakes and need to delete expenses.
**Decision:** Financial records are never physically `DELETE`d. We use `is_deleted` and `deleted_reason` fields.
**Reason:** Hard deletes destroy history and break audit trails. Soft deletes preserve historical integrity, prevent orphan records, and pair perfectly with the Audit Log.

## 11. Database Choice: PostgreSQL over SQLite
**Context:** Choosing a relational database for a production environment.
**Decision:** PostgreSQL.
**Reason:** SQLite locks the entire database during writes, which is detrimental to concurrent requests (e.g., when multiple users upload CSVs or add expenses simultaneously). PostgreSQL provides row-level locking, rich JSONB support for audit logs, and handles production concurrency gracefully.

## 12. Handling Inconsistent Duplicates
**Context:** An import row has the same date and description as an existing expense, but a different amount.
**Decision:** Flag as `INCONSISTENT_DUPLICATE` rather than silently updating or ignoring.
**Reason:** It could be a typo in the CSV, or two separate events (e.g., two Uber rides on the same day). The user must manually review and decide whether to skip the row or approve the fix.

## 13. Separating Settlements from Expenses
**Context:** Users paying each other back to settle debts.
**Decision:** Created a distinct `settlements` table.
**Reason:** Recording a settlement as a "negative expense" fundamentally breaks the data model because a settlement doesn't have "split types" or "shares" — it is purely a ledger transfer from User A to User B. Distinct tables simplify balance calculations.

## 14. Anomaly Approval Flow (Meera's Requirement)
**Context:** The CSV import process is prone to messy data, and users need a way to review issues before polluting the database.
**Decision:** Implemented a two-phase commit pattern. The CSV is parsed into temporary JSON `import_anomalies` records. The UI presents them to the user to choose "Approve Fix", "Approve Delete", or "Skip".
**Reason:** This ensures the database is never mutated until the user explicitly resolves every single error and clicks "Finalize Import", satisfying the atomic guarantee.

