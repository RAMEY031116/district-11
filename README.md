# District 11

A mobile-friendly household portal built with Streamlit + Supabase.

## Included

- Shared shopping list: add, mark bought, undo, delete, and share the latest unbought list to WhatsApp.
- Shared expenses: record who paid and exactly which household members shared the cost.
- Exact money handling in integer pence.
- Automatic weekly balances and minimum-transfer "who owes who" settlement.
- WhatsApp-ready weekly breakdown and individual payment messages.
- Mark settlement as paid and immediately recalculate balances.
- Paid settlement history.
- Reminders/calendar shown both on Home and on the Reminders page.
- Recurring bills and "record bill as paid" into expenses.
- Household members and optional WhatsApp phone numbers.
- Always-visible navigation, visible forms, dark theme and phone-friendly layout.

## GitHub files

Keep these in the repository:

- `app.py`
- `calculations.py`
- `db.py`
- `requirements.txt`
- `.gitignore`
- `.streamlit/config.toml`
- `README.md`

Do **not** commit `.streamlit/secrets.toml`.

## Streamlit Cloud secrets

In Streamlit Cloud > App settings > Secrets:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "sb_secret_YOUR_SECRET_KEY"
```

There is no household PIN in this release.

## Supabase permission fix

If Streamlit reports `permission denied for table households`, run this once in Supabase SQL Editor:

```sql
grant usage on schema public to service_role;
grant select, insert, update, delete on all tables in schema public to service_role;
alter default privileges in schema public
grant select, insert, update, delete on tables to service_role;
```

Your existing District 11 tables are used; the app does not need a database file in GitHub.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## WhatsApp behavior

The WhatsApp buttons open WhatsApp with the latest message already prepared. On your phone, choose your existing household group and press Send. This does not require the paid WhatsApp Business API.

## v8 UI fixes
- Replaced the old paid-only weekly chart with a proper live balance view.
- Each member now shows Paid, Fair share, and Owes/Receives.
- Added a dark-mode Altair balance chart with positive/negative balances.
- Strengthened Streamlit input styling so typed text, placeholders, dates, times and number fields remain readable in dark mode.
- Money remains exact to the penny; no floating-point decimal artefacts are shown.
