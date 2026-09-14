# District 11

A mobile-friendly shared household portal built with Streamlit + Supabase.

## Features
- Shopping list with mark-bought / undo / delete
- Shared expenses and exact pence-based splitting
- Automatic weekly balances and minimum settlement transfers
- WhatsApp-ready shopping and weekly settlement messages
- Mark settlement as paid + history
- Reminders/calendar with optional times and `.ics` export
- Recurring bills
- Household members and WhatsApp numbers
- Dark theme and mobile-friendly layout

## Streamlit Cloud secrets
Add these in **App settings → Secrets**:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "sb_secret_..."
```

No household PIN is required.

## Supabase permissions
If you see `permission denied for table households`, run this once in Supabase SQL Editor:

```sql
grant usage on schema public to service_role;
grant select, insert, update, delete on all tables in schema public to service_role;
alter default privileges in schema public grant select, insert, update, delete on tables to service_role;
```

## Run locally
```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```
