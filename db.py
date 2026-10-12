from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable
from functools import wraps

import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_client() -> Client:
    try:
        url = st.secrets['SUPABASE_URL']
        key = st.secrets['SUPABASE_KEY']
    except Exception as exc:
        raise RuntimeError(
            'Missing SUPABASE_URL or SUPABASE_KEY in Streamlit secrets.'
        ) from exc
    return create_client(url, key)


def _data(response):
    return response.data or []


# Short read cache avoids network requests on every Streamlit widget rerun.
# Each successful write clears these reads, so the person saving sees fresh data.
_cached_reads = []


def cached_read(ttl=15):
    def decorate(function):
        cached = st.cache_data(ttl=ttl, max_entries=64, show_spinner=False)(function)
        _cached_reads.append(cached)
        return cached
    return decorate


def refresh_after_write(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        finally:
            # Invalidate even if a multi-step write only partially completed.
            for read in _cached_reads:
                read.clear()
    return wrapped


@cached_read(ttl=300)
def get_or_create_household(name: str = 'District 11') -> dict:
    client = get_client()
    existing = _data(client.table('households').select('*').eq('name', name).limit(1).execute())
    if existing:
        household = existing[0]
    else:
        household = _data(client.table('households').insert({'name': name}).execute())[0]

    # Members are stored in Supabase; do not publish or hard-code their names.
    # Existing member IDs, expense history and balances remain unchanged.
    # Add or update household members directly in the protected database.
    return household


@cached_read()
def list_members(household_id: str) -> list[dict]:
    return _data(
        get_client().table('members')
        .select('*')
        .eq('household_id', household_id)
        .order('created_at')
        .execute()
    )


@refresh_after_write
def add_member(household_id: str, name: str, phone_number: str | None = None):
    payload = {'household_id': household_id, 'name': name.strip()}
    if phone_number:
        payload['phone_number'] = phone_number.strip()
    return _data(get_client().table('members').insert(payload).execute())[0]


@refresh_after_write
def update_member(member_id: str, **fields):
    clean = {k: v for k, v in fields.items() if v is not None}
    return _data(get_client().table('members').update(clean).eq('id', member_id).execute())


@cached_read()
def list_shopping(household_id: str) -> list[dict]:
    return _data(
        get_client().table('shopping_items')
        .select('*')
        .eq('household_id', household_id)
        .order('is_bought')
        .order('created_at', desc=True)
        .execute()
    )


@refresh_after_write
def add_shopping_item(household_id: str, item_name: str, quantity: str, added_by_member_id: str | None):
    payload = {
        'household_id': household_id,
        'item_name': item_name.strip(),
        'quantity': quantity.strip() or None,
        'added_by_member_id': added_by_member_id,
        'is_bought': False,
    }
    return _data(get_client().table('shopping_items').insert(payload).execute())[0]


@refresh_after_write
def mark_shopping_bought(item_id: str, member_id: str | None = None):
    return _data(
        get_client().table('shopping_items')
        .update({
            'is_bought': True,
            'bought_by_member_id': member_id,
            'bought_at': datetime.now().isoformat(),
        })
        .eq('id', item_id)
        .execute()
    )


@refresh_after_write
def reopen_shopping_item(item_id: str):
    return _data(
        get_client().table('shopping_items')
        .update({'is_bought': False, 'bought_by_member_id': None, 'bought_at': None})
        .eq('id', item_id)
        .execute()
    )


@refresh_after_write
def delete_shopping_item(item_id: str):
    get_client().table('shopping_items').delete().eq('id', item_id).execute()


@cached_read()
def list_expenses(household_id: str, start: date, end: date) -> list[dict]:
    return _data(
        get_client().table('expenses')
        .select('*')
        .eq('household_id', household_id)
        .gte('expense_date', start.isoformat())
        .lte('expense_date', end.isoformat())
        .order('expense_date', desc=True)
        .order('created_at', desc=True)
        .execute()
    )


@cached_read()
def list_all_expenses(household_id: str, limit: int | None = None) -> list[dict]:
    """Fetch the entire expense ledger using pages, not just a recent subset."""
    rows = []
    offset = 0
    page_size = 500
    while True:
        batch = _data(
            get_client().table('expenses')
            .select('*')
            .eq('household_id', household_id)
            .order('expense_date', desc=True)
            .order('id', desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows.extend(batch)
        if len(batch) < page_size or (limit is not None and len(rows) >= limit):
            return rows[:limit] if limit is not None else rows
        offset += page_size


@cached_read()
def list_splits(expense_ids: Iterable[str]) -> list[dict]:
    ids = list(expense_ids)
    if not ids:
        return []
    return _data(
        get_client().table('expense_splits')
        .select('*')
        .in_('expense_id', ids)
        .execute()
    )


@refresh_after_write
def add_expense(
    household_id: str,
    paid_by_member_id: str,
    description: str,
    amount_pence: int,
    expense_date: date,
    split_shares: dict[str, int],
):
    client = get_client()
    expense = _data(client.table('expenses').insert({
        'household_id': household_id,
        'paid_by_member_id': paid_by_member_id,
        'description': description.strip(),
        'amount_pence': int(amount_pence),
        'expense_date': expense_date.isoformat(),
    }).execute())[0]

    rows = [
        {'expense_id': expense['id'], 'member_id': member_id, 'share_pence': int(share)}
        for member_id, share in split_shares.items()
    ]
    if rows:
        client.table('expense_splits').insert(rows).execute()
    return expense


@refresh_after_write
def delete_expense(expense_id: str):
    # expense_splits cascade on delete.
    get_client().table('expenses').delete().eq('id', expense_id).execute()


@cached_read()
def list_settlements(household_id: str, week_start: date | None = None) -> list[dict]:
    """Read all confirmed payments, optionally filtering a display-only week."""
    rows = []
    offset = 0
    page_size = 500
    while True:
        batch = _data(get_client().table('settlements')
                      .select('*').eq('household_id', household_id)
                      .eq('status', 'paid').order('paid_at', desc=True)
                      .order('id', desc=True)
                      .range(offset, offset + page_size - 1).execute())
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    if week_start is None:
        return rows
    week_end = week_start + timedelta(days=6)
    return [row for row in rows
            if week_start <= date.fromisoformat(str(row.get('paid_at') or row.get('created_at'))[:10]) <= week_end]


@refresh_after_write
def mark_settlement_paid(
    household_id: str,
    from_member_id: str,
    to_member_id: str,
    amount_pence: int,
    week_start: date,
):
    # The original District 11 schema does not require a week_start column.
    # We group settlements into weeks by paid_at, so this works with the tables
    # you already created in Supabase.
    payload = {
        'household_id': household_id,
        'from_member_id': from_member_id,
        'to_member_id': to_member_id,
        'amount_pence': int(amount_pence),
        'status': 'paid',
        'paid_at': datetime.now().isoformat(),
    }
    return _data(get_client().table('settlements').insert(payload).execute())[0]


@cached_read()
def list_events(household_id: str, start: date | None = None, end: date | None = None) -> list[dict]:
    query = get_client().table('household_events').select('*').eq('household_id', household_id)
    if start:
        query = query.gte('event_date', start.isoformat())
    if end:
        query = query.lte('event_date', end.isoformat())
    return _data(query.order('event_date').order('event_time').execute())


@refresh_after_write
def add_event(household_id: str, title: str, description: str, event_date: date, event_time):
    payload = {
        'household_id': household_id,
        'title': title.strip(),
        'description': description.strip() or None,
        'event_date': event_date.isoformat(),
        'event_time': event_time.strftime('%H:%M:%S') if event_time else None,
    }
    return _data(get_client().table('household_events').insert(payload).execute())[0]


@refresh_after_write
def delete_event(event_id: str):
    get_client().table('household_events').delete().eq('id', event_id).execute()


@cached_read()
def list_bills(household_id: str) -> list[dict]:
    return _data(
        get_client().table('recurring_bills')
        .select('*')
        .eq('household_id', household_id)
        .order('due_day')
        .execute()
    )


@refresh_after_write
def add_bill(household_id: str, name: str, amount_pence: int, due_day: int, paid_by_member_id: str | None):
    payload = {
        'household_id': household_id,
        'name': name.strip(),
        'amount_pence': int(amount_pence),
        'due_day': int(due_day),
        'paid_by_member_id': paid_by_member_id,
    }
    return _data(get_client().table('recurring_bills').insert(payload).execute())[0]


@refresh_after_write
def delete_bill(bill_id: str):
    get_client().table('recurring_bills').delete().eq('id', bill_id).execute()

