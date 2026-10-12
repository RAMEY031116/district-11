"""All-time household statements. Amounts use the app's integer-pence ledger."""
import csv
from io import BytesIO, StringIO
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
from calculations import calculate_balances, minimize_transfers, money


def build_statement(members, expenses, splits, settlements, member_id=None):
    confirmed = [p for p in settlements if p.get('status') == 'paid']
    grouped = defaultdict(list)
    for split in splits:
        grouped[split['expense_id']].append(split)
    balances = calculate_balances(members, expenses, grouped, confirmed)
    transfers = minimize_transfers(balances)
    names = {m['id']: m['name'] for m in members}
    name = lambda mid: names.get(mid, 'Unknown member')
    if member_id is not None and member_id not in names:
        raise ValueError('Unknown statement member')
    personal = member_id is not None
    title = f"Personal statement - {name(member_id)}" if personal else 'All-time household statement'
    shown_members = [m for m in members if not personal or m['id'] == member_id]
    shown_expenses = [e for e in expenses if not personal or e['paid_by_member_id'] == member_id
                      or any(x['member_id'] == member_id for x in grouped[e['id']])]
    shown_payments = [p for p in confirmed if not personal or member_id in (p['from_member_id'], p['to_member_id'])]
    shown_transfers = [t for t in transfers if not personal or member_id in (t['from_member_id'], t['to_member_id'])]
    generated = datetime.now(ZoneInfo('Europe/London')).strftime('%d %b %Y, %H:%M %Z')
    totals = [('Total expenses', sum(int(e['amount_pence']) for e in expenses)),
              ('Confirmed payments', sum(int(p['amount_pence']) for p in confirmed)),
              ('Pending debt', sum(int(t['amount_pence']) for t in transfers))]
    if personal:
        totals = [
            ('Expenses you paid (full purchases)', sum(int(e['amount_pence']) for e in expenses if e['paid_by_member_id'] == member_id)),
            ('Your expense shares', sum(int(x['share_pence']) for x in splits if x['member_id'] == member_id)),
            ('Confirmed payments sent', sum(int(p['amount_pence']) for p in confirmed if p['from_member_id'] == member_id)),
            ('Confirmed payments received', sum(int(p['amount_pence']) for p in confirmed if p['to_member_id'] == member_id)),
            ('You owe', max(0, -balances.get(member_id, 0))),
            ('You are owed', max(0, balances.get(member_id, 0))),
        ]
    # A rectangular CSV; filter Record type to avoid mixing totals with ledger rows.
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Record type', 'Date', 'Description', 'Person / From', 'To / Shared with', 'Amount GBP', 'Personal share GBP'])
    def row(kind, day, description, person, other, pence, own_share=None):
        def safe(value):
            text = str(value or '')
            return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text
        writer.writerow([safe(v) for v in (kind, day, description, person, other)] + [f'{int(pence)/100:.2f}', '' if own_share is None else f'{int(own_share)/100:.2f}'])
    for label, amount in totals:
        row('Total', generated, label, '', '', amount)
    for member in shown_members:
        row('Balance', generated, 'Positive = receives; negative = owes', member['name'], '', balances.get(member['id'], 0))
    for t in shown_transfers:
        row('Pending payment', generated, 'Still outstanding', name(t['from_member_id']), name(t['to_member_id']), t['amount_pence'])
    expense_rows = []
    for e in sorted(shown_expenses, key=lambda e: str(e['expense_date'])):
        shared = ', '.join(f"{name(x['member_id'])}: {money(x['share_pence'])}" for x in grouped[e['id']])
        own_share = sum(int(x['share_pence']) for x in grouped[e['id']] if x['member_id'] == member_id) if personal else None
        row('Expense', str(e['expense_date'])[:10], e['description'], name(e['paid_by_member_id']), shared, e['amount_pence'], own_share)
        expense_rows.append([str(e['expense_date'])[:10], e['description'], name(e['paid_by_member_id']), money(e['amount_pence']), money(own_share) if personal else shared])
    payment_rows = []
    for payment in sorted(shown_payments, key=lambda p: str(p.get('paid_at') or p.get('created_at') or '')):
        day = str(payment.get('paid_at') or payment.get('created_at') or '')[:10]
        row('Confirmed payment', day, 'Receipt confirmed', name(payment['from_member_id']), name(payment['to_member_id']), payment['amount_pence'])
        payment_rows.append([day, name(payment['from_member_id']), name(payment['to_member_id']), money(payment['amount_pence'])])
    csv_bytes = output.getvalue().encode('utf-8-sig')

    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    pdf = BytesIO()
    doc = SimpleDocTemplate(pdf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=38, bottomMargin=38,
                            title='District 11 - Household statement', author='District 11')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Cell', fontName='Helvetica', fontSize=8, leading=11, wordWrap='CJK'))
    styles['Title'].textColor = colors.HexColor('#9d174d')
    content = [Paragraph('District 11', styles['Title']), Paragraph(escape(title), styles['Heading2']),
               Paragraph(escape(f'Generated {generated} | All recorded weeks'), styles['Normal']), Spacer(1, 14)]
    def table(headers, rows, widths):
        cells = [[Paragraph(escape(str(v)), styles['Cell']) for v in r] for r in [headers] + rows]
        t = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT', splitInRow=1)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fce7f3')),
                              ('VALIGN',(0,0),(-1,-1),'TOP'), ('BOTTOMPADDING',(0,0),(-1,-1),7),
                              ('TOPPADDING',(0,0),(-1,-1),7),
                              ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#ec4899')),
                              ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#e5e7eb'))]))
        content.append(t)
        content.append(Spacer(1, 12))
    table(['Summary', 'Amount'], [[label, money(amount)] for label, amount in totals], [383, 140])
    content.append(Paragraph('Who owes whom', styles['Heading2']))
    table(['From', 'To', 'Still owed'], [[name(t['from_member_id']), name(t['to_member_id']), money(t['amount_pence'])] for t in shown_transfers]
          or [['No pending payments', '-', money(0)]], [191, 192, 140])
    content.append(Paragraph('Balances', styles['Heading2']))
    table(['Member', 'Status', 'Amount'], [[m['name'], 'Receives' if balances.get(m['id'],0)>0 else 'Owes' if balances.get(m['id'],0)<0 else 'Settled', money(abs(balances.get(m['id'],0)))] for m in shown_members], [191,192,140])
    content.append(Paragraph('Expense history', styles['Heading2']))
    table(['Date', 'Description', 'Paid by', 'Full amount', 'Your share' if personal else 'Shares'], expense_rows or [['-', 'No expenses recorded', '-', money(0), '-']], [63,145,80,65,170])
    content.append(Paragraph('Confirmed payment history', styles['Heading2']))
    table(['Date', 'From', 'To', 'Received'], payment_rows or [['-', 'No confirmed payments', '-', money(0)]], [80,151,152,140])
    content.append(Paragraph('Balances carry forward until receipt is confirmed. Totals describe separate measures and should not be added together. Shared amounts use the app’s equal-share rounding.', styles['Normal']))
    def footer(canvas, document):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(36,22,'District 11 | All amounts in GBP')
        canvas.drawRightString(A4[0]-36,22,f'Page {document.page}')
    doc.build(content,onFirstPage=footer,onLaterPages=footer)
    return pdf.getvalue(), csv_bytes

