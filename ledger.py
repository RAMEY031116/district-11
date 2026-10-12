"""Explain the same net balance calculation used by the payment suggestions."""
from collections import defaultdict


def member_ledger(member_id, expenses, splits, settlements, names):
    grouped = defaultdict(list)
    for split in splits:
        grouped[split['expense_id']].append(split)
    rows = []
    for expense in expenses:
        shares = grouped[expense['id']]
        own_share = sum(int(s['share_pence']) for s in shares if s['member_id'] == member_id)
        payer = expense['paid_by_member_id'] == member_id
        if not payer and not any(s['member_id'] == member_id for s in shares):
            continue
        credit = sum(int(s['share_pence']) for s in shares) if payer else 0
        rows.append({'date': str(expense['expense_date'])[:10], 'description': expense['description'],
                     'detail': f"Paid by {names.get(expense['paid_by_member_id'], 'Unknown')}",
                     'credit_pence': credit, 'share_pence': own_share,
                     'change_pence': credit - own_share})
    for payment in settlements:
        if payment.get('status') != 'paid':
            continue
        outgoing = payment['from_member_id'] == member_id
        incoming = payment['to_member_id'] == member_id
        if not outgoing and not incoming:
            continue
        other = payment['to_member_id'] if outgoing else payment['from_member_id']
        change = int(payment['amount_pence']) * (int(outgoing) - int(incoming))
        rows.append({'date': str(payment.get('paid_at') or payment.get('created_at') or '')[:10],
                     'description': 'Payment sent' if outgoing else 'Payment received',
                     'detail': names.get(other, 'Unknown'), 'credit_pence': 0, 'share_pence': 0,
                     'change_pence': change})
    rows.sort(key=lambda row: row['date'])
    running = 0
    for row in rows:
        running += row['change_pence']
        row['balance_pence'] = running
    return rows
