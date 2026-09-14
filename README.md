# District 11

Private shared household portal built with Streamlit and Supabase.

## GitHub files

The deployed app only needs:

- `app.py`
- `calculations.py`
- `db.py`
- `requirements.txt`
- `README.md`
- `.gitignore` (recommended)

Your live database stays in Supabase. Do not put credentials in GitHub.

## Streamlit Secrets

District 11 no longer uses a household PIN/unlock screen.

Add only these secrets in Streamlit Community Cloud:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "sb_secret_YOUR_SECRET_KEY"
```

## Fix: permission denied for table households (42501)

If Streamlit reaches Supabase but shows `permission denied for table households`, open Supabase -> SQL Editor and run:

```sql
grant usage on schema public to service_role;

grant select, insert, update, delete
on all tables in schema public
to service_role;

alter default privileges in schema public
grant select, insert, update, delete
on tables to service_role;
```

Then reboot the Streamlit app.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Security

`SUPABASE_KEY` is a server-side secret. Keep it only in Streamlit Secrets/local secret storage and never commit it to GitHub.
