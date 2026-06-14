"""Balance calculation engine and minimum-transactions settlement algorithm.

Implements the exact logic from the prompt:
1. Credit payers, debit split members (only if active on expense date)
2. Apply settlements
3. Generate minimum-transaction settlement suggestions via greedy matching

All arithmetic uses Python Decimal — never float.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.expense import ExpenseSplit
from app.models.group import GroupMember
from app.models.settlement import Settlement


def is_member_active_on_date(
    user_id: UUID, group_id: UUID, check_date: date, db: Session
) -> bool:
    """Check if a user was an active group member on a given date."""
    membership = (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
        .first()
    )
    if membership is None:
        return False
    return membership.is_active_on(check_date)


def get_active_expenses(
    group_id: UUID, db: Session, as_of_date: date | None = None
) -> list[Expense]:
    """Get all non-deleted expenses for a group, optionally filtered by date."""
    query = db.query(Expense).filter(
        Expense.group_id == group_id,
        Expense.is_deleted == False,  # noqa: E712
    )
    if as_of_date is not None:
        query = query.filter(Expense.date <= as_of_date)
    return query.all()


def get_settlements(
    group_id: UUID, db: Session, as_of_date: date | None = None
) -> list[Settlement]:
    """Get all settlements for a group."""
    query = db.query(Settlement).filter(Settlement.group_id == group_id)
    if as_of_date is not None:
        query = query.filter(Settlement.recorded_at <= as_of_date)
    return query.all()


def calculate_balances(
    group_id: UUID, db: Session, as_of_date: date | None = None
) -> dict[UUID, Decimal]:
    """
    Calculate net balances for all members of a group.

    Returns dict: { user_id: net_balance_inr }
    Positive = this person is owed money
    Negative = this person owes money
    """
    balances: dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))

    expenses = get_active_expenses(group_id, db, as_of_date)
    for expense in expenses:
        # Credit the payer the full amount in INR
        balances[expense.paid_by_user_id] += expense.amount_in_inr

        # Debit each person their split share
        # Only include members active on the expense date
        for split in expense.splits:
            if is_member_active_on_date(split.user_id, group_id, expense.date, db):
                balances[split.user_id] -= split.share_amount_inr

    # Apply settlements
    settlements = get_settlements(group_id, db, as_of_date)
    for s in settlements:
        balances[s.from_user_id] += s.amount_inr   # payer's debt reduced
        balances[s.to_user_id] -= s.amount_inr     # receiver's credit reduced

    return dict(balances)


def suggest_settlements(
    balances: dict[UUID, Decimal]
) -> list[dict]:
    """
    Minimum transactions algorithm using greedy matching.

    Sort creditors and debtors by magnitude, then match the biggest
    debtor to the biggest creditor, transferring the minimum of the two.
    Repeat until all balances are settled.
    """
    # Build sorted lists of creditors and debtors
    creditors = sorted(
        [(v, k) for k, v in balances.items() if v > Decimal("0.01")],
        reverse=True,
    )
    debtors = sorted(
        [(abs(v), k) for k, v in balances.items() if v < Decimal("-0.01")],
        reverse=True,
    )

    transactions = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        credit_amount, creditor_id = creditors[i]
        debt_amount, debtor_id = debtors[j]

        # Transfer the smaller of the two amounts
        transfer = min(credit_amount, debt_amount)

        if transfer > Decimal("0.01"):  # Skip negligible amounts
            transactions.append({
                "from_user_id": debtor_id,
                "to_user_id": creditor_id,
                "amount_inr": transfer.quantize(Decimal("0.01")),
            })

        # Update remaining amounts
        creditors[i] = (credit_amount - transfer, creditor_id)
        debtors[j] = (debt_amount - transfer, debtor_id)

        # Move to next if settled
        if creditors[i][0] <= Decimal("0.01"):
            i += 1
        if debtors[j][0] <= Decimal("0.01"):
            j += 1

    return transactions


def get_balance_breakdown(
    user_id: UUID, group_id: UUID, db: Session
) -> list[dict]:
    """
    Rohan's drilldown: per-expense breakdown showing each expense's
    contribution to a user's balance.

    Returns a list of expense records with the user's role (payer/ower)
    and their specific share amount.
    """
    expenses = get_active_expenses(group_id, db)
    breakdown = []

    for expense in expenses:
        entry = {
            "expense_id": expense.id,
            "description": expense.description,
            "date": expense.date,
            "total_amount": expense.total_amount,
            "currency": expense.currency,
            "amount_in_inr": expense.amount_in_inr,
            "paid_by_user_id": expense.paid_by_user_id,
            "impact": Decimal("0"),
        }

        # Did this user pay?
        if expense.paid_by_user_id == user_id:
            entry["impact"] += expense.amount_in_inr

        # What is this user's share?
        for split in expense.splits:
            if split.user_id == user_id:
                if is_member_active_on_date(user_id, group_id, expense.date, db):
                    entry["impact"] -= split.share_amount_inr
                    entry["user_share_inr"] = split.share_amount_inr

        # Only include expenses that affect this user
        if entry["impact"] != Decimal("0") or "user_share_inr" in entry:
            breakdown.append(entry)

    return breakdown
