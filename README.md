# District 11

A private shared-house portal built with **Streamlit + Supabase**.

## Features

- Shared shopping list
- Mark shopping items bought / undo
- Record expenses in real money (integer pence)
- Select who paid and exactly who should share each cost
- Automatic weekly balances
- Minimum-transfer settlement calculation
- Weekly balance chart
- WhatsApp-ready weekly summary
- One-tap WhatsApp payment message to a saved phone number
- Mark a settlement as paid and recalculate instantly
- Settlement history for each week
- Shared calendar/reminders
- Download reminders as an `.ics` calendar file
- Recurring bills
- Record a bill as a normal shared expense
- Household member/phone-number management
- Shared household PIN instead of individual accounts
- Mobile-friendly layout

## 1. Update your existing Supabase project

Because you already created the tables, run:

`migrate_existing_project.sql`

in **Supabase -> SQL Editor**.

If starting from a completely empty project instead, run `supabase_schema.sql`.

## 2. Supabase API credentials

In Supabase, copy:

- Project URL
- Server-side secret/service-role key

Do **not** commit the secret key to GitHub.

The Streamlit app uses the server-side key so RLS can remain enabled without forcing everyone in the house to create individual accounts. Protect the app with the shared `HOUSEHOLD_PIN` and keep the Streamlit secrets private.

## 3. Run locally

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_KEY = "YOUR-SERVER-SIDE-SUPABASE-SECRET-KEY"
HOUSEHOLD_PIN = "your-private-pin"
```

Then:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## 4. Push to GitHub

```bash
git init
git add .
git commit -m "Initial District 11 portal"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/district11.git
git push -u origin main
```

`.streamlit/secrets.toml` is already ignored by `.gitignore`.

## 5. Deploy on Streamlit Community Cloud

1. Create a new app from the GitHub repository.
2. Main file: `app.py`
3. Open **App settings -> Secrets**.
4. Paste:

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_KEY = "YOUR-SERVER-SIDE-SUPABASE-SECRET-KEY"
HOUSEHOLD_PIN = "your-private-pin"
```

5. Deploy.

District 11 automatically creates the `District 11` household and ensures **Bipesh, Sabin and Yush** exist if they are missing. It does not create fake expenses or shopping data.

## WhatsApp limitation

The app can open WhatsApp with the correct shopping list, weekly breakdown, or payment request already filled in. You can then choose your existing household group and tap Send. Direct payment buttons can also open a specific person's WhatsApp chat if their phone number is saved.

It does **not** silently post into an existing WhatsApp group in the background. Doing that reliably requires WhatsApp Business Platform capabilities and has restrictions that are not suitable for a simple private household group.
