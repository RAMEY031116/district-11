# District 11

A simple shared household portal built with Streamlit + Supabase.

## Included now

- Home dashboard
- Shared shopping list
- Mark shopping items bought / undo / delete
- Open WhatsApp with the current **unbought** shopping list ready to share
- Shared expenses
- Choose who paid and who shared each expense
- Simple equal-looking rounded splitting (e.g. £20 / 3 = £6.67 each)
- Weekly balance and minimum settle-up transfers
- Open WhatsApp with the current outstanding weekly balance ready to share
- Mark settlements paid and keep payment history
- Reminders/calendar
- Dark theme and mobile-friendly layout

Bills and household-management screens are intentionally hidden for now to keep the portal simple.

## Streamlit secrets

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "sb_secret_..."
```

Keep the secret key in Streamlit Secrets only. Do not commit it to GitHub.

## GitHub files

- `app.py`
- `calculations.py`
- `db.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `.gitignore`

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```


## Equal split rule
District 11 deliberately uses the same rounded share for every selected person. For example, £20.00 split between three people is shown as £6.67 each. A tiny rounding adjustment (1p in this example) is absorbed into the settlement basis so one person is not shown a different share.

## WhatsApp sharing
The Shopping and Balance pages use green WhatsApp-style share buttons. Shopping shares only items still marked as not bought. Balance shares the current outstanding settlement.
