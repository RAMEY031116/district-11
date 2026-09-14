from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from urllib.parse import quote

import pandas as pd
import streamlit as st

import db
from calculations import calculate_balances, equal_split, minimize_transfers, money, to_pence, week_bounds

st.set_page_config(
    page_title='District 11',
    page_icon='🏠',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# ---------- Dark portal styling ----------
st.markdown(
    r'''
    <style>
    :root {
      color-scheme: dark;
      --bg:#090d14; --bg2:#0d131d; --panel:#111827; --panel2:#151f2e;
      --ink:#f8fafc; --muted:#94a3b8; --line:#253246; --accent:#60a5fa;
      --green:#34d399; --red:#fb7185; --amber:#fbbf24;
    }

    html, body, [class*="css"] {
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
      background: radial-gradient(circle at top left, #111a29 0, var(--bg) 34rem);
      color:var(--ink);
    }
    .block-container { max-width:1220px; padding-top:1rem; padding-bottom:5rem; }

    /* Sidebar */
    [data-testid="stSidebar"] { background:#080c12; border-right:1px solid #1f2a3a; }
    [data-testid="stSidebar"] * { color:var(--ink); }

    /* General text */
    h1,h2,h3,h4,h5,h6,p,label,span,div { color:inherit; }
    .stCaption, [data-testid="stCaptionContainer"] { color:var(--muted) !important; }

    /* Inputs: force readable white text on dark controls */
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-baseweb="select"] > div,
    [data-baseweb="base-input"],
    [data-testid="stDateInput"] > div > div,
    [data-testid="stNumberInput"] > div > div {
      background:#0c1420 !important;
      border-color:#334155 !important;
      color:var(--ink) !important;
    }
    input, textarea, [contenteditable="true"] {
      color:#f8fafc !important;
      -webkit-text-fill-color:#f8fafc !important;
      caret-color:#f8fafc !important;
      background:transparent !important;
    }
    input::placeholder, textarea::placeholder {
      color:#64748b !important;
      -webkit-text-fill-color:#64748b !important;
      opacity:1 !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [role="option"],
    [role="listbox"] * {
      color:#f8fafc !important;
    }
    [role="listbox"] { background:#111827 !important; }

    /* Forms, expanders, metrics, alerts */
    [data-testid="stForm"],
    [data-testid="stExpander"] details,
    [data-testid="stMetric"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
      background:rgba(17,24,39,.94) !important;
      border:1px solid var(--line) !important;
      border-radius:18px !important;
      box-shadow:0 12px 36px rgba(0,0,0,.2);
    }
    [data-testid="stMetric"] { padding:15px 17px; }
    [data-testid="stMetric"] * { color:var(--ink) !important; }
    [data-testid="stMetricDelta"] * { color:var(--muted) !important; }

    /* Buttons */
    .stButton > button, .stLinkButton > a, [data-testid="stDownloadButton"] button {
      border-radius:12px !important;
      min-height:43px;
      font-weight:750 !important;
      border:1px solid #334155 !important;
      background:#162235 !important;
      color:#f8fafc !important;
    }
    .stButton > button:hover, .stLinkButton > a:hover, [data-testid="stDownloadButton"] button:hover {
      border-color:#60a5fa !important;
      background:#1d2c43 !important;
      color:white !important;
    }
    button[kind="primary"] {
      background:#2563eb !important;
      border-color:#3b82f6 !important;
      color:white !important;
    }

    /* Tabs / radio */
    [data-testid="stRadio"] label, [data-testid="stCheckbox"] label { color:var(--ink) !important; }

    /* Portal surfaces */
    .hero {
      padding:26px 28px; border-radius:24px;
      background:linear-gradient(135deg,#111827,#16243a 58%,#1d3555);
      border:1px solid #263a59; box-shadow:0 18px 52px rgba(0,0,0,.28); margin-bottom:18px;
    }
    .hero * { color:#fff !important; }
    .hero-kicker { font-size:.78rem; opacity:.7; text-transform:uppercase; letter-spacing:.13em; font-weight:800; }
    .hero-title { font-size:2.15rem; line-height:1.06; font-weight:850; margin:.35rem 0 .55rem; }
    .hero-sub { font-size:.98rem; opacity:.82; max-width:820px; }
    .card {
      background:linear-gradient(180deg,#111827,#0f1724); border:1px solid var(--line);
      border-radius:18px; padding:17px; margin-bottom:10px; box-shadow:0 10px 30px rgba(0,0,0,.16);
    }
    .card-title { color:var(--ink); font-weight:800; font-size:1rem; }
    .card-sub { color:var(--muted); font-size:.84rem; margin-top:3px; }
    .pill { display:inline-block; border-radius:999px; padding:.25rem .6rem; background:#172554; color:#bfdbfe; font-size:.75rem; font-weight:750; }
    .receive { color:var(--green) !important; font-weight:850; }
    .owe { color:var(--red) !important; font-weight:850; }
    .settled { color:var(--green) !important; font-weight:850; }

    /* Data editor/table internals */
    [data-testid="stDataFrame"] * { color:#e5e7eb; }

    @media (max-width: 768px) {
      .block-container { padding:.7rem .72rem 5rem; }
      .hero { padding:20px 18px; border-radius:18px; }
      .hero-title { font-size:1.55rem; }
      .hero-sub { font-size:.9rem; }
      [data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
      [data-testid="stHorizontalBlock"] { gap:.65rem !important; flex-wrap:wrap !important; }
      .stButton > button, .stLinkButton > a, [data-testid="stDownloadButton"] button { width:100%; min-height:47px; }
      h1 { font-size:1.7rem !important; } h2 { font-size:1.35rem !important; } h3 { font-size:1.08rem !important; }
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


try:
    household = db.get_or_create_household('District 11')
    members = db.list_members(household['id'])
except Exception as exc:
    message = str(exc)
    st.error('District 11 cannot connect to Supabase.')
    st.code(message)
    if 'permission denied' in message.lower() or "42501" in message:
        st.warning('Your Supabase URL/key are being reached, but the database role does not have permission to read the tables. Run the GRANT SQL shown in the setup instructions, then reboot the Streamlit app.')
    else:
        st.info('Check SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets, then reboot the app.')
    st.stop()

member_by_id = {m['id']: m for m in members}
member_name = {m['id']: m['name'] for m in members}
member_id_by_name = {m['name']: m['id'] for m in members}


# ---------- Helpers ----------
def whatsapp_share_url(text: str) -> str:
    return f"https://wa.me/?text={quote(text)}"


def direct_whatsapp_url(phone: str | None, text: str) -> str | None:
    if not phone:
        return None
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if not digits:
        return None
    return f"https://wa.me/{digits}?text={quote(text)}"


def parse_db_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def current_week_data(selected_start: date):
    selected_end = selected_start + timedelta(days=6)
    expenses = db.list_expenses(household['id'], selected_start, selected_end)
    splits = db.list_splits([e['id'] for e in expenses])
    splits_by_expense = defaultdict(list)
    for row in splits:
        splits_by_expense[row['expense_id']].append(row)
    settlements = [s for s in db.list_settlements(household['id'], selected_start) if s.get('status') == 'paid']
    balances = calculate_balances(members, expenses, splits_by_expense, settlements)
    transfers = minimize_transfers(balances)
    return selected_end, expenses, splits_by_expense, settlements, balances, transfers


def shopping_text(shopping: list[dict]) -> str:
    active = [item for item in shopping if not item.get('is_bought')]
    lines = ['🛒 District 11 shopping list']
    if not active:
        lines.append('Everything is bought ✅')
    else:
        lines.append('')
        for item in active:
            qty = f" ({item['quantity']})" if item.get('quantity') else ''
            lines.append(f"• {item['item_name']}{qty}")
    return '\n'.join(lines)


def weekly_summary(selected_start: date, selected_end: date, expenses, splits_by_expense, settlements, transfers, shopping) -> str:
    lines = [
        f"🏠 District 11 weekly summary ({selected_start:%d %b}–{selected_end:%d %b})",
        '',
        f"Total household spend: {money(sum(int(e['amount_pence']) for e in expenses))}",
    ]
    if expenses:
        lines.append('\nPaid this week:')
        for member in members:
            paid = sum(int(e['amount_pence']) for e in expenses if e['paid_by_member_id'] == member['id'])
            lines.append(f"• {member['name']}: {money(paid)}")

        lines.append('\nBreakdown:')
        for expense in sorted(expenses, key=lambda e: e['expense_date']):
            split_names = ', '.join(member_name.get(s['member_id'], 'Unknown') for s in splits_by_expense.get(expense['id'], []))
            lines.append(
                f"• {expense['description']}: {money(expense['amount_pence'])} — "
                f"{member_name.get(expense['paid_by_member_id'], 'Unknown')} paid — for {split_names}"
            )

    if settlements:
        lines.append('\nAlready paid:')
        for s in reversed(settlements):
            lines.append(
                f"• {member_name.get(s['from_member_id'], 'Unknown')} → "
                f"{member_name.get(s['to_member_id'], 'Unknown')}: {money(s['amount_pence'])} ✅"
            )

    lines.append('\nOutstanding settlement:')
    if transfers:
        for t in transfers:
            lines.append(
                f"• {member_name[t['from_member_id']]} → {member_name[t['to_member_id']]}: {money(t['amount_pence'])}"
            )
    else:
        lines.append('• Everyone is settled ✅')

    active = [i for i in shopping if not i.get('is_bought')]
    if active:
        lines.append('\nStill to buy:')
        for item in active[:25]:
            qty = f" ({item['quantity']})" if item.get('quantity') else ''
            lines.append(f"• {item['item_name']}{qty}")
    return '\n'.join(lines)


def make_ics(events: list[dict]) -> str:
    chunks = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//District 11//Household Calendar//EN']
    for event in events:
        uid = f"{event['id']}@district11"
        day = parse_db_date(event['event_date'])
        event_time = event.get('event_time')
        chunks.extend(['BEGIN:VEVENT', f'UID:{uid}'])
        if event_time:
            hhmm = str(event_time)[:5].replace(':', '')
            chunks.append(f"DTSTART:{day:%Y%m%d}T{hhmm}00")
        else:
            chunks.append(f"DTSTART;VALUE=DATE:{day:%Y%m%d}")
        chunks.append(f"SUMMARY:{event['title'].replace(',', '\\,')}")
        if event.get('description'):
            chunks.append(f"DESCRIPTION:{event['description'].replace(',', '\\,')}")
        chunks.append('END:VEVENT')
    chunks.append('END:VCALENDAR')
    return '\r\n'.join(chunks)


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('## 🏠 District 11')
    st.caption('Shared home portal')
    page = st.radio(
        'Navigate',
        ['Home', 'Shopping', 'Expenses', 'Balance', 'Calendar', 'Bills', 'Household'],
        label_visibility='collapsed',
    )
    st.divider()
    st.caption('Members')
    st.write(' · '.join(m['name'] for m in members))


# ---------- Shared week selector ----------
current_start, _ = week_bounds()


# ---------- HOME ----------
if page == 'Home':
    shopping = db.list_shopping(household['id'])
    week_end, expenses, splits_by_expense, settlements, balances, transfers = current_week_data(current_start)
    upcoming_events = db.list_events(household['id'], date.today(), date.today() + timedelta(days=14))
    bills = db.list_bills(household['id'])

    st.markdown(
        '''<div class="hero"><div class="hero-kicker">Household operating system</div>
        <div class="hero-title">District 11</div>
        <div class="hero-sub">Shopping, spending, balances, bills and reminders in one shared place.</div></div>''',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Spent this week', money(sum(int(e['amount_pence']) for e in expenses)))
    c2.metric('Shopping left', str(sum(1 for x in shopping if not x.get('is_bought'))))
    c3.metric('Transfers left', str(len(transfers)))
    c4.metric('Upcoming reminders', str(len(upcoming_events)))

    st.subheader('This week at a glance')
    if expenses:
        chart_rows = []
        for member in members:
            paid = sum(int(e['amount_pence']) for e in expenses if e['paid_by_member_id'] == member['id'])
            chart_rows.append({'Person': member['name'], 'Paid (£)': paid / 100})
        chart_df = pd.DataFrame(chart_rows).set_index('Person')
        st.bar_chart(chart_df, use_container_width=True)
    else:
        st.info('No expenses have been added for this week yet.')

    left, right = st.columns(2)
    with left:
        st.subheader('Settle up')
        if transfers:
            for transfer in transfers:
                st.markdown(
                    f"<div class='card'><div class='card-title'>{member_name[transfer['from_member_id']]} → {member_name[transfer['to_member_id']]}</div>"
                    f"<div class='card-sub'>{money(transfer['amount_pence'])} still outstanding</div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success('Everyone is settled for this week ✅')

    with right:
        st.subheader('Coming up')
        if upcoming_events:
            for event in upcoming_events[:6]:
                when = parse_db_date(event['event_date']).strftime('%a %d %b')
                if event.get('event_time'):
                    when += f" · {str(event['event_time'])[:5]}"
                st.markdown(
                    f"<div class='card'><div class='card-title'>{event['title']}</div><div class='card-sub'>{when}</div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption('No reminders in the next 14 days.')

    if bills:
        st.subheader('Regular bills')
        cols = st.columns(min(3, len(bills)))
        for idx, bill in enumerate(bills[:6]):
            with cols[idx % len(cols)]:
                st.metric(bill['name'], money(bill['amount_pence']), f"Due day {bill['due_day']}")


# ---------- SHOPPING ----------
elif page == 'Shopping':
    st.title('🛒 Shopping')
    st.caption('Add something the moment you remember it. Anyone can mark it bought later.')
    shopping = db.list_shopping(household['id'])

    with st.form('add_shopping', clear_on_submit=True):
        a, b, c = st.columns([2, 1, 1])
        item_name = a.text_input('Item', placeholder='Milk, rice, washing liquid…')
        quantity = b.text_input('Quantity', placeholder='2 packs')
        added_by_name = c.selectbox('Added by', [m['name'] for m in members])
        submitted = st.form_submit_button('Add to list', type='primary', use_container_width=True)
        if submitted:
            if not item_name.strip():
                st.error('Enter an item name.')
            else:
                db.add_shopping_item(household['id'], item_name, quantity, member_id_by_name[added_by_name])
                st.rerun()

    active = [x for x in shopping if not x.get('is_bought')]
    bought = [x for x in shopping if x.get('is_bought')]

    st.link_button('📲 Share current list on WhatsApp', whatsapp_share_url(shopping_text(shopping)), use_container_width=True)

    st.subheader(f'To buy · {len(active)}')
    if not active:
        st.success('Everything on the list has been bought ✅')
    for item in active:
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            qty = f" · {item['quantity']}" if item.get('quantity') else ''
            added_by = member_name.get(item.get('added_by_member_id'), 'House')
            c1.markdown(f"**{item['item_name']}**{qty}")
            c1.caption(f"Added by {added_by}")
            buyer_name = c2.selectbox('Bought by', [m['name'] for m in members], key=f"buyer_{item['id']}")
            b1, b2 = c2.columns(2)
            if b1.button('✓ Bought', key=f"bought_{item['id']}", use_container_width=True):
                db.mark_shopping_bought(item['id'], member_id_by_name[buyer_name])
                st.rerun()
            if b2.button('Delete', key=f"delete_shop_{item['id']}", use_container_width=True):
                db.delete_shopping_item(item['id'])
                st.rerun()

    with st.expander(f'Bought items · {len(bought)}'):
        for item in bought[:50]:
            who = member_name.get(item.get('bought_by_member_id'), 'Someone')
            c1, c2 = st.columns([4, 1])
            c1.write(f"✅ {item['item_name']} — {who}")
            if c2.button('Undo', key=f"undo_{item['id']}", use_container_width=True):
                db.reopen_shopping_item(item['id'])
                st.rerun()


# ---------- EXPENSES ----------
elif page == 'Expenses':
    st.title('💳 Expenses')
    st.caption('Record who paid and who benefited. District 11 works out the balance automatically.')

    with st.form('add_expense', clear_on_submit=True):
        a, b = st.columns(2)
        description = a.text_input('What was it?', placeholder='Tesco groceries')
        amount = b.number_input('Amount (£)', min_value=0.01, step=0.01, format='%.2f')
        c, d = st.columns(2)
        payer_name = c.selectbox('Who paid?', [m['name'] for m in members])
        expense_day = d.date_input('Date', value=date.today())
        split_names = st.multiselect(
            'Who should share this cost?',
            [m['name'] for m in members],
            default=[m['name'] for m in members],
            help='Select only the people who benefited from this purchase.',
        )
        submitted = st.form_submit_button('Add expense', type='primary', use_container_width=True)
        if submitted:
            if not description.strip():
                st.error('Enter a description.')
            elif not split_names:
                st.error('Choose at least one person to split the expense with.')
            else:
                amount_pence = to_pence(amount)
                split_ids = [member_id_by_name[name] for name in split_names]
                db.add_expense(
                    household['id'],
                    member_id_by_name[payer_name],
                    description,
                    amount_pence,
                    expense_day,
                    equal_split(amount_pence, split_ids),
                )
                st.rerun()

    start = st.date_input('Show week starting', value=current_start, key='expenses_week')
    end, expenses, splits_by_expense, _, _, _ = current_week_data(start)
    st.subheader(f'{start:%d %b} – {end:%d %b}')
    if not expenses:
        st.info('No expenses in this week.')
    for expense in expenses:
        split_names = ', '.join(member_name.get(row['member_id'], 'Unknown') for row in splits_by_expense.get(expense['id'], []))
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1.2, 1])
            c1.markdown(f"**{expense['description']}**")
            c1.caption(f"{member_name.get(expense['paid_by_member_id'], 'Unknown')} paid · split with {split_names} · {expense['expense_date']}")
            c2.markdown(f"### {money(expense['amount_pence'])}")
            if c3.button('Delete', key=f"del_exp_{expense['id']}", use_container_width=True):
                db.delete_expense(expense['id'])
                st.rerun()


# ---------- BALANCE ----------
elif page == 'Balance':
    st.title('⚖️ Balance')
    st.caption('The app nets everything together so nobody sends money back and forth unnecessarily.')

    selected_start = st.date_input('Week starting', value=current_start, key='balance_week')
    selected_end, expenses, splits_by_expense, settlements, balances, transfers = current_week_data(selected_start)
    shopping = db.list_shopping(household['id'])

    c1, c2, c3 = st.columns(3)
    c1.metric('Household spend', money(sum(int(e['amount_pence']) for e in expenses)))
    c2.metric('Paid settlements', money(sum(int(s['amount_pence']) for s in settlements)))
    c3.metric('Transfers remaining', str(len(transfers)))

    chart_rows = []
    for member in members:
        chart_rows.append({'Person': member['name'], 'Balance (£)': balances.get(member['id'], 0) / 100})
    chart_df = pd.DataFrame(chart_rows).set_index('Person')
    st.subheader('Live balance')
    st.bar_chart(chart_df, use_container_width=True)

    cols = st.columns(max(1, min(3, len(members))))
    for idx, member in enumerate(members):
        balance = balances.get(member['id'], 0)
        with cols[idx % len(cols)]:
            if balance > 0:
                st.metric(member['name'], money(balance), 'should receive')
            elif balance < 0:
                st.metric(member['name'], money(balance), 'owes')
            else:
                st.metric(member['name'], '£0.00', 'settled')

    summary = weekly_summary(selected_start, selected_end, expenses, splits_by_expense, settlements, transfers, shopping)
    st.link_button('📲 Share weekly summary on WhatsApp', whatsapp_share_url(summary), type='primary', use_container_width=True)

    st.subheader('Settle up')
    if not transfers:
        st.success('Everyone is settled for this week ✅')
    for idx, transfer in enumerate(transfers):
        sender = member_by_id[transfer['from_member_id']]
        receiver = member_by_id[transfer['to_member_id']]
        text = (
            f"🏠 District 11\n\n{sender['name']} → {receiver['name']}: {money(transfer['amount_pence'])}\n"
            f"Week {selected_start:%d %b}–{selected_end:%d %b}\n\n"
            "Please send this when you can. Once paid, mark it as paid in District 11 ✅"
        )
        with st.container(border=True):
            left, right = st.columns([2.2, 1.5])
            left.markdown(f"### {sender['name']} → {receiver['name']}")
            left.markdown(f"## {money(transfer['amount_pence'])}")
            direct_url = direct_whatsapp_url(sender.get('phone_number'), text)
            if direct_url:
                right.link_button('📲 WhatsApp payer', direct_url, use_container_width=True)
            else:
                right.link_button('📲 Share payment', whatsapp_share_url(text), use_container_width=True)
            if right.button(
                f"✓ Mark {money(transfer['amount_pence'])} paid",
                key=f"settle_{selected_start}_{idx}_{sender['id']}_{receiver['id']}",
                type='primary',
                use_container_width=True,
            ):
                db.mark_settlement_paid(
                    household['id'], sender['id'], receiver['id'], transfer['amount_pence'], selected_start
                )
                st.success('Payment recorded. Balances have been recalculated.')
                st.rerun()

    st.subheader('Paid this week')
    if not settlements:
        st.caption('No settlement payments have been recorded yet.')
    else:
        for settlement in settlements:
            paid_at = str(settlement.get('paid_at', ''))[:16].replace('T', ' ')
            st.markdown(
                f"<div class='card'><div class='card-title'>✅ {member_name.get(settlement['from_member_id'], 'Unknown')} → "
                f"{member_name.get(settlement['to_member_id'], 'Unknown')} · {money(settlement['amount_pence'])}</div>"
                f"<div class='card-sub'>{paid_at}</div></div>",
                unsafe_allow_html=True,
            )


# ---------- CALENDAR ----------
elif page == 'Calendar':
    st.title('📅 Calendar & reminders')
    st.caption('Keep house appointments, chores and reminders together.')

    with st.form('add_event', clear_on_submit=True):
        a, b = st.columns(2)
        title = a.text_input('Reminder / event', placeholder='Bin day, inspection, dinner…')
        event_date = b.date_input('Date', value=date.today())
        c, d = st.columns(2)
        has_time = c.checkbox('Add a time')
        event_time = d.time_input('Time', value=time(18, 0), disabled=not has_time)
        description = st.text_area('Notes', placeholder='Optional details')
        submitted = st.form_submit_button('Add to calendar', type='primary', use_container_width=True)
        if submitted:
            if not title.strip():
                st.error('Enter a title.')
            else:
                db.add_event(household['id'], title, description, event_date, event_time if has_time else None)
                st.rerun()

    events = db.list_events(household['id'], date.today() - timedelta(days=30), date.today() + timedelta(days=365))
    if events:
        st.download_button(
            '⬇️ Download calendar (.ics)',
            data=make_ics(events),
            file_name='district11-calendar.ics',
            mime='text/calendar',
            use_container_width=True,
        )
    upcoming = [e for e in events if parse_db_date(e['event_date']) >= date.today()]
    st.subheader('Upcoming')
    if not upcoming:
        st.info('No upcoming reminders.')
    for event in upcoming[:50]:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            when = parse_db_date(event['event_date']).strftime('%A %d %B')
            if event.get('event_time'):
                when += f" · {str(event['event_time'])[:5]}"
            c1.markdown(f"**{event['title']}**")
            c1.caption(when)
            if event.get('description'):
                c1.write(event['description'])
            if c2.button('Delete', key=f"del_event_{event['id']}", use_container_width=True):
                db.delete_event(event['id'])
                st.rerun()


# ---------- BILLS ----------
elif page == 'Bills':
    st.title('🧾 Regular bills')
    st.caption('Keep the recurring house costs visible and add them to expenses when they are paid.')

    with st.form('add_bill', clear_on_submit=True):
        a, b, c = st.columns(3)
        bill_name = a.text_input('Bill', placeholder='WiFi, rent, council tax…')
        bill_amount = b.number_input('Amount (£)', min_value=0.01, step=0.01, format='%.2f')
        due_day = c.number_input('Due day', min_value=1, max_value=31, value=1, step=1)
        payer = st.selectbox('Usually paid by', ['Not fixed'] + [m['name'] for m in members])
        submitted = st.form_submit_button('Add regular bill', type='primary', use_container_width=True)
        if submitted:
            if not bill_name.strip():
                st.error('Enter a bill name.')
            else:
                db.add_bill(
                    household['id'], bill_name, to_pence(bill_amount), int(due_day),
                    member_id_by_name.get(payer) if payer != 'Not fixed' else None,
                )
                st.rerun()

    bills = db.list_bills(household['id'])
    if not bills:
        st.info('No regular bills added yet.')
    for bill in bills:
        with st.container(border=True):
            a, b, c = st.columns([3, 1.2, 1.5])
            a.markdown(f"**{bill['name']}**")
            a.caption(f"Due on day {bill['due_day']} · usually paid by {member_name.get(bill.get('paid_by_member_id'), 'not fixed')}")
            b.markdown(f"### {money(bill['amount_pence'])}")
            if c.button('Delete', key=f"del_bill_{bill['id']}", use_container_width=True):
                db.delete_bill(bill['id'])
                st.rerun()

    if bills:
        st.subheader('Record a bill as paid')
        selected_bill_name = st.selectbox('Bill', [b['name'] for b in bills], key='paid_bill_name')
        selected_bill = next(b for b in bills if b['name'] == selected_bill_name)
        payer_default = member_name.get(selected_bill.get('paid_by_member_id'), members[0]['name'])
        payer_name = st.selectbox('Paid by', [m['name'] for m in members], index=[m['name'] for m in members].index(payer_default) if payer_default in [m['name'] for m in members] else 0, key='paid_bill_payer')
        split_names = st.multiselect('Split between', [m['name'] for m in members], default=[m['name'] for m in members], key='paid_bill_split')
        paid_date = st.date_input('Paid date', value=date.today(), key='paid_bill_date')
        if st.button('Add this bill to expenses', type='primary', use_container_width=True):
            split_ids = [member_id_by_name[n] for n in split_names]
            if not split_ids:
                st.error('Choose at least one person to split the bill with.')
            else:
                db.add_expense(
                    household['id'],
                    member_id_by_name[payer_name],
                    selected_bill['name'],
                    int(selected_bill['amount_pence']),
                    paid_date,
                    equal_split(int(selected_bill['amount_pence']), split_ids),
                )
                st.success('Bill added to expenses.')
                st.rerun()


# ---------- HOUSEHOLD ----------
elif page == 'Household':
    st.title('🏡 Household')
    st.caption('Manage who is in District 11 and save WhatsApp numbers for one-tap payment messages.')

    for member in members:
        with st.container(border=True):
            c1, c2 = st.columns([1.2, 2])
            c1.markdown(f"### {member['name']}")
            phone = c2.text_input(
                'WhatsApp number',
                value=member.get('phone_number') or '',
                placeholder='+447123456789',
                key=f"phone_{member['id']}",
                help='Use international format. Example: +447123456789',
            )
            if c2.button('Save number', key=f"save_phone_{member['id']}", use_container_width=True):
                db.update_member(member['id'], phone_number=phone.strip() or None)
                st.success(f"Saved {member['name']}'s number.")
                st.rerun()

    with st.expander('Add another person'):
        with st.form('add_member', clear_on_submit=True):
            name = st.text_input('Name')
            phone = st.text_input('WhatsApp number', placeholder='+44…')
            submitted = st.form_submit_button('Add person', type='primary', use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error('Enter a name.')
                elif name.strip().lower() in {m['name'].lower() for m in members}:
                    st.error('That person already exists.')
                else:
                    db.add_member(household['id'], name, phone)
                    st.rerun()

    st.divider()
    st.subheader('Deployment status')
    st.success('District 11 is using Supabase for shared data.')
    st.caption('GitHub stores the code. Streamlit runs the site. Supabase stores the household data.')
    st.warning('Automatic scheduled WhatsApp group posting is not included. WhatsApp share buttons open a ready-written message so you can choose your existing group and send it.')
