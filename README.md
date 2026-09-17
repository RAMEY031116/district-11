# District 11

Simple shared household portal using Streamlit + Supabase.

## Current features

- Home dashboard
- Shopping list with no “added by” requirement
- Add an item + optional quantity
- One-tap **Bought ✓** button
- Bought items move out of the active list
- Undo or delete shopping items
- WhatsApp share contains only items still left to buy
- Shared expenses and automatic equal-looking split
- Weekly balance and who-pays-who settlement
- Mark settlements paid
- WhatsApp balance sharing
- Reminders
- Dark/mobile-friendly UI

Shopping is intentionally simple: names are not recorded for who added or bought an item. Names remain on expenses because they are required for balance calculations.

## Streamlit secrets

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "sb_secret_..."
```
