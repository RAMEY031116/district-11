# District 11

Simple shared household portal using Streamlit + Supabase.

## Current features

- Home dashboard
- Shopping list with no “added by” requirement
- Add an item + optional quantity
- One-tap **Bought ✓** button; unbought items carry forward across weeks
- Bought items move out of the active list
- Undo or delete shopping items
- WhatsApp share contains only items still left to buy
- Shared expenses and automatic equal-looking split
- Weekly spending history plus a cumulative outstanding balance that carries across weeks
- Recipient confirms money received before a settlement clears
- WhatsApp balance sharing
- Reminders
- Dark/mobile-friendly UI

Shopping is intentionally simple: names are not recorded for who added or bought an item. Names remain on expenses because they are required for balance calculations.

## Streamlit secrets

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "sb_secret_..."
```

## Manual balance settlement

Outstanding balances never reset at the start of a week. The selected week only changes the activity report. Payments are recorded only when the recipient confirms receipt in the Balance section. Full and partial payments are supported; the remaining amount carries forward until it reaches zero. The Balance section also contains complete recorded payment history. No database schema migration is needed.
