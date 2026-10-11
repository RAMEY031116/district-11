from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from urllib.parse import quote

from html import escape
import streamlit as st

import db
from calculations import calculate_balances, equal_split, minimize_transfers, money, to_pence, week_bounds

st.set_page_config(
    page_title='District 11',
    page_icon='D',
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

    /* Inputs - force a consistent dark field surface and readable typing. */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
      background:#0b1220 !important;
      color:#f8fafc !important;
      -webkit-text-fill-color:#f8fafc !important;
      caret-color:#f8fafc !important;
      border-color:#334155 !important;
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stNumberInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder,
    [data-testid="stDateInput"] input::placeholder,
    [data-testid="stTimeInput"] input::placeholder,
    input::placeholder, textarea::placeholder {
      color:#8191a8 !important;
      -webkit-text-fill-color:#8191a8 !important;
      opacity:1 !important;
    }
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"],
    div[data-baseweb="select"] > div,
    [data-testid="stTextInput"] > div > div,
    [data-testid="stNumberInput"] > div > div,
    [data-testid="stDateInput"] > div > div,
    [data-testid="stTimeInput"] > div > div {
      background:#0b1220 !important;
      border-color:#334155 !important;
      color:#f8fafc !important;
    }
    [data-baseweb="select"] *, [role="option"], [role="listbox"] * { color:#f8fafc !important; }
    [role="listbox"] { background:#111827 !important; }
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus {
      -webkit-box-shadow:0 0 0 1000px #0b1220 inset !important;
      -webkit-text-fill-color:#f8fafc !important;
    }

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

    /* Clean pill navigation: no radio circles. */
    [data-testid="stSegmentedControl"] { margin:.15rem 0 .25rem; }
    [data-testid="stSegmentedControl"] button {
      border-radius:999px !important;
      min-height:40px !important;
      padding:.45rem .9rem !important;
      font-weight:750 !important;
    }

    @media (max-width: 768px) {
      .block-container { padding:.7rem .72rem 5rem; }
      .hero { padding:20px 18px; border-radius:18px; }
      .hero-title { font-size:1.55rem; }
      .hero-sub { font-size:.9rem; }
      [data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
      [data-testid="stHorizontalBlock"] { gap:.65rem !important; flex-wrap:wrap !important; }
      .stButton > button, .stLinkButton > a, [data-testid="stDownloadButton"] button { width:100%; min-height:47px; }
      h1 { font-size:1.7rem !important; } h2 { font-size:1.35rem !important; } h3 { font-size:1.08rem !important; }
      [data-testid="stRadio"] > div { flex-wrap:wrap !important; gap:.35rem !important; }
    }

    .brand { font-size:1.2rem; font-weight:850; letter-spacing:-.04em; }
    .brand-number { color:#93c5fd; }
    .brand-label { margin-left:.6rem; font-size:.9rem; letter-spacing:0; }
    .hero { box-shadow:none; padding:32px; background:linear-gradient(120deg,#142338,#101b2b); }
    .hero-title { letter-spacing:-.035em; font-size:2.4rem; }
    [class*="st-key-shortcut_"] button {
      width:100%; min-height:112px; padding:18px !important; text-align:left;
      justify-content:flex-start; background:linear-gradient(145deg,#17253a,#111c2c) !important;
      border:1px solid #30435c !important; border-radius:18px !important;
      transition:background .15s,border-color .15s;
    }
    [class*="st-key-shortcut_"] button p { text-align:left; white-space:pre-line; font-size:1rem; line-height:1.6; }
    [class*="st-key-shortcut_"] button:hover { background:#20334d !important; border-color:#93c5fd !important; }
    .st-key-shortcut_home_debt button { border-color:#806546 !important; }
    button:focus-visible, a:focus-visible { outline:3px solid #93c5fd !important; outline-offset:3px; }
    [data-testid="stVerticalBlockBorderWrapper"] > div { border-radius:16px; }
    [data-testid="stForm"] { box-shadow:none; }
    [data-testid="stSegmentedControl"] button { min-height:46px !important; }
    @media (max-width:768px) {
      .hero-title { font-size:1.8rem; }
      .brand-label { display:none; }
      [data-testid="stColumn"] { min-width:100% !important; flex:1 1 100% !important; }
      .block-container { padding-bottom:calc(7rem + env(safe-area-inset-bottom)); }
      .st-key-app_navigation {
        position:fixed; bottom:0; left:0; right:0; z-index:999;
        background:#0d1726; border-top:1px solid #30435c;
        padding:10px 8px calc(10px + env(safe-area-inset-bottom));
        box-shadow:0 -8px 24px rgba(0,0,0,.25);
      }
      .st-key-app_navigation [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; gap:4px !important; }
      .st-key-app_navigation [data-testid="stColumn"] {
        width:auto !important; min-width:0 !important; flex:1 1 0 !important;
      }
      .st-key-app_navigation button {
        flex:1 1 0; min-width:0; min-height:48px !important;
        padding:8px 5px !important; border-radius:12px !important;
      }
      .st-key-app_navigation button p { font-size:.75rem; }
      [class*="st-key-shortcut_"] button { min-height:92px; }
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


def whatsapp_button(label: str, text: str, *, phone: str | None = None) -> None:
    """Render a clean WhatsApp-style share button with an inline icon."""
    url = direct_whatsapp_url(phone, text) if phone else whatsapp_share_url(text)
    if not url:
        url = whatsapp_share_url(text)
    safe_url = escape(url, quote=True)
    safe_label = escape(label)
    st.markdown(
        f"""
        <a href="{safe_url}" target="_blank" rel="noopener noreferrer"
           style="display:flex;align-items:center;justify-content:center;gap:10px;width:100%;
                  min-height:46px;box-sizing:border-box;border-radius:12px;padding:10px 16px;
                  background:#25D366;color:#07130b;text-decoration:none;font-weight:850;
                  border:1px solid #39df79;box-shadow:0 8px 22px rgba(37,211,102,.14);">
          <svg aria-hidden="true" width="21" height="21" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="white"/>
            <path d="M8.4 7.2c.25-.55.52-.56.77-.57h.65c.2 0 .42.08.52.34l.79 1.92c.09.22.05.42-.07.61l-.47.65c-.13.17-.27.32-.12.58.15.26.67 1.08 1.46 1.75 1 .87 1.84 1.14 2.1 1.27.26.13.41.11.57-.07l.85-.99c.2-.23.4-.19.67-.09l1.73.82c.27.13.45.19.52.3.07.11.07.63-.15 1.24-.22.61-1.28 1.17-1.76 1.24-.45.07-1.02.1-1.65-.1-.38-.12-.86-.28-1.48-.55a8.92 8.92 0 0 1-3.55-3.12c-.96-1.31-1.61-2.93-1.66-3.06-.05-.13-.5-1.33.24-2.02Z" fill="#25D366"/>
          </svg>
          <span>{safe_label}</span>
        </a>
        """,
        unsafe_allow_html=True,
    )


def parse_db_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def current_week_data(selected_start: date):
    """Return weekly activity plus the household's cumulative outstanding balance.

    A week boundary is only for reporting. Unpaid debt must carry forward until
    the recipient explicitly confirms that the money was received.
    """
    selected_end = selected_start + timedelta(days=6)

    # Weekly activity: used for the selected week's spend/history only.
    expenses = db.list_expenses(household['id'], selected_start, selected_end)
    weekly_splits = db.list_splits([e['id'] for e in expenses])
    splits_by_expense = defaultdict(list)
    for row in weekly_splits:
        splits_by_expense[row['expense_id']].append(row)
    settlements = [s for s in db.list_settlements(household['id'], selected_start) if s.get('status') == 'paid']

    # Outstanding ledger: ALL expenses minus ALL confirmed receipts. This is
    # deliberately not filtered by week, so Monday never resets money owed.
    all_expenses = db.list_all_expenses(household['id'])
    all_splits = db.list_splits([e['id'] for e in all_expenses])
    all_splits_by_expense = defaultdict(list)
    for row in all_splits:
        all_splits_by_expense[row['expense_id']].append(row)
    all_confirmed_settlements = [
        s for s in db.list_settlements(household['id']) if s.get('status') == 'paid'
    ]
    balances = calculate_balances(members, all_expenses, all_splits_by_expense, all_confirmed_settlements)
    transfers = minimize_transfers(balances)

    return selected_end, expenses, splits_by_expense, settlements, balances, transfers


def shopping_text(shopping: list[dict]) -> str:
    active = [item for item in shopping if not item.get('is_bought')]
    lines = [' District 11 shopping list']
    if not active:
        lines.append('Everything is bought ')
    else:
        lines.append('')
        for item in active:
            qty = f" ({item['quantity']})" if item.get('quantity') else ''
            lines.append(f"{item['item_name']}{qty}")
    return '\n'.join(lines)


def weekly_summary(selected_start: date, selected_end: date, expenses, splits_by_expense, settlements, transfers, shopping) -> str:
    lines = [
        f" District 11 weekly summary ({selected_start:%d %b}-{selected_end:%d %b})",
        '',
        f"Total household spend: {money(sum(int(e['amount_pence']) for e in expenses))}",
    ]
    if expenses:
        lines.append('\nPaid this week:')
        for member in members:
            paid = sum(int(e['amount_pence']) for e in expenses if e['paid_by_member_id'] == member['id'])
            lines.append(f"{member['name']}: {money(paid)}")

        lines.append('\nBreakdown:')
        for expense in sorted(expenses, key=lambda e: e['expense_date']):
            split_names = ', '.join(member_name.get(s['member_id'], 'Unknown') for s in splits_by_expense.get(expense['id'], []))
            lines.append(
                f"{expense['description']}: {money(expense['amount_pence'])} - "
                f"{member_name.get(expense['paid_by_member_id'], 'Unknown')} paid - for {split_names}"
            )

    if settlements:
        lines.append('\nAlready paid:')
        for s in reversed(settlements):
            lines.append(
                f"{member_name.get(s['from_member_id'], 'Unknown')} to "
                f"{member_name.get(s['to_member_id'], 'Unknown')}: {money(s['amount_pence'])} "
            )

    lines.append('\nOutstanding settlement:')
    if transfers:
        for t in transfers:
            lines.append(
                f"{member_name[t['from_member_id']]} to {member_name[t['to_member_id']]}: {money(t['amount_pence'])}"
            )
    else:
        lines.append('Everyone is settled ')

    active = [i for i in shopping if not i.get('is_bought')]
    if active:
        lines.append('\nStill to buy:')
        for item in active[:25]:
            qty = f" ({item['quantity']})" if item.get('quantity') else ''
            lines.append(f"{item['item_name']}{qty}")
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


def member_week_stats(expenses, splits_by_expense, balances):
    """Return exact paid/fair-share/balance figures in pence for each member."""
    rows = []
    for member in members:
        member_id = member['id']
        paid = sum(int(e['amount_pence']) for e in expenses if e['paid_by_member_id'] == member_id)
        fair_share = sum(
            int(split['share_pence'])
            for expense in expenses
            for split in splits_by_expense.get(expense['id'], [])
            if split['member_id'] == member_id
        )
        rows.append({
            'id': member_id,
            'name': member['name'],
            'paid': paid,
            'fair_share': fair_share,
            'balance': int(balances.get(member_id, 0)),
        })
    return rows



def render_balance_visual(stats):
    """Render a dependency-free balance visual that works reliably on Streamlit Cloud."""
    if not stats:
        st.caption('No balance data yet.')
        return

    maximum = max([abs(int(row['balance'])) for row in stats] + [1])
    rows = []
    for row in stats:
        balance = int(row['balance'])
        width = max(2, round(abs(balance) / maximum * 48)) if balance else 0
        name = escape(str(row['name']))
        amount = escape(money(abs(balance)))

        if balance > 0:
            left_bar = ''
            right_bar = f'<div style="width:{width}%;height:16px;border-radius:0 9px 9px 0;background:#34d399;"></div>'
            status = f'<span style="color:#34d399;font-weight:800">+{amount} receives</span>'
        elif balance < 0:
            left_bar = f'<div style="width:{width}%;height:16px;border-radius:9px 0 0 9px;background:#fb7185;margin-left:auto;"></div>'
            right_bar = ''
            status = f'<span style="color:#fb7185;font-weight:800">-{amount} owes</span>'
        else:
            left_bar = ''
            right_bar = ''
            status = '<span style="color:#34d399;font-weight:800">£0.00 settled</span>'

        rows.append(
            '<div style="margin:14px 0 18px">'
            '<div style="display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:7px">'
            f'<strong style="color:#f8fafc">{name}</strong>{status}'
            '</div>'
            '<div style="display:grid;grid-template-columns:1fr 1px 1fr;align-items:center;min-height:16px">'
            f'<div>{left_bar}</div>'
            '<div style="width:1px;height:25px;background:#64748b"></div>'
            f'<div>{right_bar}</div>'
            '</div></div>'
        )

    st.markdown(
        "<div class='card'><div class='card-sub' style='margin-bottom:.4rem'>Owes ← <span style='padding:0 .5rem'>£0</span> to Receives</div>"
        + ''.join(rows)
        + "</div>",
        unsafe_allow_html=True,
    )


# ---------- Navigation ----------
NAV_OPTIONS = ['Home', 'Shopping', 'Expenses', 'Balance', 'Reminders']
NAV_KEY = 'top_navigation'


def navigate(destination: str, transfer=None) -> None:
    """Callbacks run before widgets render, keeping the visible navigation in sync."""
    st.session_state[NAV_KEY] = destination
    st.session_state['focused_transfer'] = transfer


def dashboard_shortcut(label: str, value: str, detail: str, destination: str, key: str) -> None:
    with st.container(key=f'shortcut_{key}'):
        st.button(f'{label} · {value}\n\n{detail} →', key=key,
                  on_click=navigate, args=(destination,), use_container_width=True)


if NAV_KEY not in st.session_state:
    st.session_state[NAV_KEY] = 'Home'

# ---------- Simple navigation ----------
st.markdown(
    "<div style='display:flex;align-items:center;justify-content:space-between;gap:1rem;margin:.1rem 0 .65rem'>"
    "<span class='brand'>D<span class='brand-number'>11</span> <span class='brand-label'>District 11</span></span>"
    f"<span style='color:#94a3b8;font-size:.82rem'>{escape(' · '.join(m['name'] for m in members))}</span>"
    "</div>",
    unsafe_allow_html=True,
)

with st.container(key='app_navigation'):
    nav_columns = st.columns(len(NAV_OPTIONS))
    for nav_column, destination in zip(nav_columns, NAV_OPTIONS):
        nav_column.button(destination, key=f'nav_{destination.lower()}',
                          type='primary' if st.session_state[NAV_KEY] == destination else 'secondary',
                          on_click=navigate, args=(destination,), use_container_width=True)
page = st.session_state[NAV_KEY]
st.divider()


# ---------- Shared week selector ----------
current_start, _ = week_bounds()


# ---------- HOME ----------
if page == 'Home':
    shopping = db.list_shopping(household['id'])
    week_end, expenses, splits_by_expense, settlements, balances, transfers = current_week_data(current_start)
    upcoming_events = db.list_events(household['id'], date.today(), date.today() + timedelta(days=14))

    st.caption(f'THIS WEEK · {current_start:%d %b} – {week_end:%d %b}')
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        dashboard_shortcut('Weekly spend', money(sum(int(e['amount_pence']) for e in expenses)),
                           'View expenses', 'Expenses', 'home_expenses')
    with c2:
        dashboard_shortcut('Shopping left', str(sum(1 for x in shopping if not x.get('is_bought'))),
                           'Open shopping list', 'Shopping', 'home_shopping')
    with c3:
        dashboard_shortcut('Pending debt', money(sum(t['amount_pence'] for t in transfers)),
                           f'{len(transfers)} payments · Settle up', 'Balance', 'home_debt')
    with c4:
        dashboard_shortcut('Coming up', str(len(upcoming_events)),
                           'View reminders', 'Reminders', 'home_reminders')
    st.caption('Pending debt includes all unpaid balances, including previous weeks.')

    # Fast phone actions: prepare live data and hand it to WhatsApp.
    home_summary = weekly_summary(current_start, week_end, expenses, splits_by_expense, settlements, transfers, shopping)
    share1, share2 = st.columns(2)
    with share1:
        whatsapp_button('Share shopping list', shopping_text(shopping))
    with share2:
        whatsapp_button('Share weekly balance', home_summary)

    with st.expander('＋ Add shopping, an expense or a reminder', expanded=False):
        quick_tab1, quick_tab2, quick_tab3 = st.tabs(['Shopping', 'Expense', 'Reminder'])

        with quick_tab1:
            with st.form('home_add_shopping', clear_on_submit=True):
                qa, qb = st.columns([2, 1])
                q_item = qa.text_input('Item', placeholder='Milk, rice, washing liquid…', key='home_shopping_item')
                q_qty = qb.text_input('Quantity', placeholder='2 packs', key='home_shopping_qty')
                if st.form_submit_button('Add to shopping list', type='primary', use_container_width=True):
                    if not q_item.strip():
                        st.error('Enter an item name.')
                    else:
                        db.add_shopping_item(household['id'], q_item, q_qty, None)
                        st.success('Added to shopping list.')
                        st.rerun()

        with quick_tab2:
            with st.form('home_add_expense', clear_on_submit=True):
                ea, eb = st.columns(2)
                q_desc = ea.text_input('What was it?', placeholder='Tesco groceries', key='home_expense_desc')
                q_amount = eb.number_input('Amount (£)', min_value=0.01, step=0.01, format='%.2f', key='home_expense_amount')
                ec, ed = st.columns(2)
                q_payer = ec.selectbox('Who paid?', [m['name'] for m in members], key='home_expense_payer')
                q_date = ed.date_input('Date', value=date.today(), key='home_expense_date')
                q_split = st.multiselect('Who should share this cost?', [m['name'] for m in members], default=[m['name'] for m in members], key='home_expense_split')
                if st.form_submit_button('Add expense', type='primary', use_container_width=True):
                    if not q_desc.strip():
                        st.error('Enter a description.')
                    elif not q_split:
                        st.error('Choose at least one person.')
                    else:
                        q_pence = to_pence(q_amount)
                        q_ids = [member_id_by_name[n] for n in q_split]
                        db.add_expense(household['id'], member_id_by_name[q_payer], q_desc, q_pence, q_date, equal_split(q_pence, q_ids))
                        st.success('Expense added.')
                        st.rerun()

        with quick_tab3:
            with st.form('home_add_reminder', clear_on_submit=True):
                ra, rb = st.columns(2)
                q_title = ra.text_input('Reminder / event', placeholder='Bin day, rent, appointment…', key='home_reminder_title')
                q_day = rb.date_input('Date', value=date.today(), key='home_reminder_date')
                rc, rd = st.columns(2)
                q_has_time = rc.checkbox('Add a time', key='home_reminder_has_time')
                q_time = rd.time_input('Time', value=time(18, 0), disabled=not q_has_time, key='home_reminder_time')
                q_notes = st.text_area('Notes', placeholder='Optional details', key='home_reminder_notes')
                if st.form_submit_button('Add reminder', type='primary', use_container_width=True):
                    if not q_title.strip():
                        st.error('Enter a reminder title.')
                    else:
                        db.add_event(household['id'], q_title, q_notes, q_day, q_time if q_has_time else None)
                        st.success('Reminder added.')
                        st.rerun()


    st.subheader('Everyone’s balance')
    stats = member_week_stats(expenses, splits_by_expense, balances)
    glance_cols = st.columns(max(1, min(3, len(stats))))
    for idx, row in enumerate(stats):
        with glance_cols[idx % len(glance_cols)]:
            if row['balance'] > 0:
                status = f"Receives {money(row['balance'])}"
                status_class = 'receive'
            elif row['balance'] < 0:
                status = f"Owes {money(abs(row['balance']))}"
                status_class = 'owe'
            else:
                status = 'Settled'
                status_class = 'settled'
            st.markdown(
                f"<div class='card'><div class='card-title'>{escape(str(row['name']))}</div>"
                f"<div class='card-sub'>This week: paid <strong>{money(row['paid'])}</strong> | share <strong>{money(row['fair_share'])}</strong></div>"
                f"<div class='{status_class}' style='margin-top:.55rem'>{status}</div></div>",
                unsafe_allow_html=True,
            )
            st.button('View balance →', key=f"home_member_{row['id']}",
                      on_click=navigate, args=('Balance',), use_container_width=True)
    if not expenses:
        st.caption('No new expenses this week. Any older unpaid balance remains outstanding until receipt is confirmed.')
    else:
        st.caption('Weekly spend resets for reporting only. Outstanding money carries forward until the recipient confirms receipt.')

    left, right = st.columns(2)
    with left:
        st.subheader('Settle up')
        if transfers:
            for idx, transfer in enumerate(transfers):
                sender = member_name[transfer['from_member_id']]
                receiver = member_name[transfer['to_member_id']]
                with st.container(key=f'shortcut_transfer_{idx}'):
                    st.button(f"{sender} owes {receiver} · {money(transfer['amount_pence'])}\n\nReview payment →",
                              key=f'home_transfer_{idx}', use_container_width=True,
                              on_click=navigate, args=('Balance', (transfer['from_member_id'], transfer['to_member_id'])))
        else:
            st.success('Everyone is fully settled.')

    with right:
        st.subheader('Coming up')
        if upcoming_events:
            today = date.today()
            tomorrow = today + timedelta(days=1)
            for event in upcoming_events[:8]:
                event_day = parse_db_date(event['event_date'])
                if event_day == today:
                    day_label = 'Today'
                elif event_day == tomorrow:
                    day_label = 'Tomorrow'
                else:
                    day_label = event_day.strftime('%a %d %b')
                when = day_label
                if event.get('event_time'):
                    when += f" | {str(event['event_time'])[:5]}"
                notes = event.get('description') or ''
                note_html = f"<div class='card-sub'>{escape(str(notes))}</div>" if notes else ''
                st.markdown(
                    f"<div class='card'><div class='card-title'> {escape(str(event['title']))}</div><div class='card-sub'>{when}</div>{note_html}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption('No reminders in the next 14 days.')



# ---------- SHOPPING ----------
elif page == 'Shopping':
    st.title('Shopping')
    st.caption('Open items carry forward until someone explicitly marks them bought. A new week never clears the list.')

    shopping = db.list_shopping(household['id'])

    with st.form('add_shopping', clear_on_submit=True):
        a, b = st.columns([2, 1])
        item_name = a.text_input('Item', placeholder='Milk, rice, washing liquid…', key='shopping_item_name')
        quantity = b.text_input('Quantity', placeholder='2 packs', key='shopping_quantity')
        submitted = st.form_submit_button('Add to list', type='primary', use_container_width=True)
        if submitted:
            if not item_name.strip():
                st.error('Enter an item name.')
            else:
                db.add_shopping_item(household['id'], item_name, quantity, None)
                st.rerun()

    active = [x for x in shopping if not x.get('is_bought')]
    bought = [x for x in shopping if x.get('is_bought')]

    whatsapp_button('Share latest shopping list', shopping_text(shopping))

    st.subheader(f'To buy | {len(active)}')
    if not active:
        st.success('Everything on the list has been bought ')
    for item in active:
        with st.container(border=True):
            c1, c2 = st.columns([4, 2])
            qty = f" | {item['quantity']}" if item.get('quantity') else ''
            c1.markdown(f"### {item['item_name']}{qty}")
            c1.caption('Still needed')
            b1, b2 = c2.columns(2)
            if b1.button('Bought ✓', key=f"bought_{item['id']}", type='primary', use_container_width=True):
                db.mark_shopping_bought(item['id'], None)
                st.rerun()
            if b2.button('Delete', key=f"delete_shop_{item['id']}", use_container_width=True):
                db.delete_shopping_item(item['id'])
                st.rerun()

    with st.expander(f'Bought | {len(bought)}', expanded=False):
        if not bought:
            st.caption('Nothing bought yet.')
        for item in bought[:50]:
            c1, c2 = st.columns([4, 1])
            qty = f" | {item['quantity']}" if item.get('quantity') else ''
            c1.write(f" {item['item_name']}{qty}")
            if c2.button('Undo', key=f"undo_{item['id']}", use_container_width=True):
                db.reopen_shopping_item(item['id'])
                st.rerun()


# ---------- EXPENSES ----------
elif page == 'Expenses':
    st.title('Expenses')
    st.caption('Record who paid and who benefited. District 11 works out the balance automatically.')


    with st.form('add_expense', clear_on_submit=True):
        a, b = st.columns(2)
        description = a.text_input('What was it?', placeholder='Tesco groceries', key='expense_description')
        amount = b.number_input('Amount (£)', min_value=0.01, step=0.01, format='%.2f', key='expense_amount')
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
    st.subheader(f'{start:%d %b} - {end:%d %b}')
    if not expenses:
        st.info('No expenses in this week.')
    for expense in expenses:
        split_names = ', '.join(member_name.get(row['member_id'], 'Unknown') for row in splits_by_expense.get(expense['id'], []))
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1.2, 1])
            c1.markdown(f"**{expense['description']}**")
            c1.caption(f"{member_name.get(expense['paid_by_member_id'], 'Unknown')} paid | split with {split_names} | {expense['expense_date']}")
            c2.markdown(f"### {money(expense['amount_pence'])}")
            if c3.button('Delete', key=f"del_exp_{expense['id']}", use_container_width=True):
                db.delete_expense(expense['id'])
                st.rerun()


# ---------- BALANCE ----------
elif page == 'Balance':
    st.title('Balance')
    st.caption('Outstanding balances carry forward across weeks and only clear when the recipient confirms the money was received.')

    selected_start = st.date_input('Activity week starting', value=current_start, key='balance_week')
    selected_end, expenses, splits_by_expense, settlements, balances, transfers = current_week_data(selected_start)
    shopping = db.list_shopping(household['id'])

    c1, c2, c3 = st.columns(3)
    c1.metric('Spend in selected week', money(sum(int(e['amount_pence']) for e in expenses)))
    c2.metric('Receipts confirmed this week', money(sum(int(s['amount_pence']) for s in settlements)))
    c3.metric('Outstanding transfers', str(len(transfers)))

    st.subheader('Settle up')
    st.caption('No automatic settlement or weekly reset. Record a payment only after the recipient has actually received it. Partial payments are supported.')
    if not transfers:
        st.success('All balances are zero. No payments are outstanding.')
    focused_transfer = st.session_state.get('focused_transfer')
    transfers = sorted(transfers, key=lambda t: (t['from_member_id'], t['to_member_id']) != focused_transfer)
    for idx, transfer in enumerate(transfers):
        sender = member_by_id[transfer['from_member_id']]
        receiver = member_by_id[transfer['to_member_id']]
        outstanding = int(transfer['amount_pence'])
        with st.container(border=True):
            if focused_transfer == (sender['id'], receiver['id']):
                st.caption('SELECTED FROM HOME')
            st.markdown(f"**{sender['name']} owes {receiver['name']}**")
            st.write(f"Outstanding: {money(outstanding)}")
            message = (f"District 11\n{sender['name']} owes {receiver['name']} {money(outstanding)}. "
                       "This amount remains due until a payment is manually confirmed.")
            whatsapp_button('Share balance', message, phone=sender.get('phone_number'))
            with st.form(f"manual_payment_{sender['id']}_{receiver['id']}"):
                payment = st.number_input('Amount received (£)', min_value=0.01,
                                          max_value=outstanding / 100, value=outstanding / 100,
                                          step=0.01, format='%.2f',
                                          key=f"payment_amount_{sender['id']}_{receiver['id']}_{outstanding}")
                confirmed = st.checkbox(f"{receiver['name']} confirms this payment was received", key=f"payment_confirm_{sender['id']}_{receiver['id']}_{outstanding}")
                submitted = st.form_submit_button('Record received payment', type='primary')
                if submitted:
                    amount_pence = to_pence(payment)
                    if not confirmed:
                        st.error('Confirm that the recipient has received the money first.')
                    elif not 0 < amount_pence <= outstanding:
                        st.error('The payment must be greater than zero and no more than the outstanding amount.')
                    else:
                        db.mark_settlement_paid(household['id'], sender['id'], receiver['id'], amount_pence, selected_start)
                        st.rerun()

    st.divider()
    stats = member_week_stats(expenses, splits_by_expense, balances)
    st.subheader('Outstanding balance')
    render_balance_visual(stats)

    cols = st.columns(max(1, min(3, len(stats))))
    for idx, row in enumerate(stats):
        with cols[idx % len(cols)]:
            if row['balance'] > 0:
                status = f"Receives {money(row['balance'])}"
                status_class = 'receive'
            elif row['balance'] < 0:
                status = f"Owes {money(abs(row['balance']))}"
                status_class = 'owe'
            else:
                status = 'Settled'
                status_class = 'settled'
            st.markdown(
                f"<div class='card'><div class='card-title'>{escape(str(row['name']))}</div>"
                f"<div class='card-sub'>Paid <strong>{money(row['paid'])}</strong></div>"
                f"<div class='card-sub'>Fair share <strong>{money(row['fair_share'])}</strong></div>"
                f"<div class='{status_class}' style='margin-top:.6rem'>{status}</div></div>",
                unsafe_allow_html=True,
            )
    st.caption('District 11 rounds to one identical share for everyone. Example: £20.00 split three ways displays £6.67 each; the 1p rounding difference is absorbed so nobody gets a different-looking share.')

    summary = weekly_summary(selected_start, selected_end, expenses, splits_by_expense, settlements, transfers, shopping)
    whatsapp_button('Share activity + outstanding balance', summary)

    st.subheader('Payment history')
    st.caption('Every manually confirmed payment is kept, including payments from previous weeks.')
    payment_history = db.list_settlements(household['id'])
    if not payment_history:
        st.caption('No payments have been recorded yet.')
    else:
        history_rows = []
        for payment in payment_history:
            paid_at = str(payment.get('paid_at') or payment.get('created_at') or '')[:16].replace('T', ' ')
            history_rows.append({
                'Date': paid_at,
                'From': member_name.get(payment['from_member_id'], 'Unknown'),
                'To': member_name.get(payment['to_member_id'], 'Unknown'),
                'Amount': money(payment['amount_pence']),
                'Status': 'Received',
            })
        st.dataframe(history_rows, use_container_width=True, hide_index=True)
        st.caption(f"Total payments recorded: {len(payment_history)}")


# ---------- CALENDAR ----------
elif page == 'Reminders':
    st.title('Reminders and calendar')
    st.caption('Add reminders, chores and house events here. They appear on the Home dashboard too.')


    with st.form('add_event', clear_on_submit=True):
        a, b = st.columns(2)
        title = a.text_input('Reminder / event', placeholder='Bin day, inspection, dinner…', key='reminder_title')
        event_date = b.date_input('Date', value=date.today())
        c, d = st.columns(2)
        has_time = c.checkbox('Add a time')
        event_time = d.time_input('Time', value=time(18, 0), disabled=not has_time)
        description = st.text_area('Notes', placeholder='Optional details', key='reminder_notes')
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
                when += f" | {str(event['event_time'])[:5]}"
            c1.markdown(f"**{event['title']}**")
            c1.caption(when)
            if event.get('description'):
                c1.write(event['description'])
            if c2.button('Delete', key=f"del_event_{event['id']}", use_container_width=True):
                db.delete_event(event['id'])
                st.rerun()

