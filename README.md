# District 11 🏠

**A shared household hub for shopping, expenses, balances and reminders.**

District 11 helps housemates keep everyday life organised in one place. Add things to buy, record shared spending, see who owes whom, confirm repayments, and keep track of upcoming household events. It is built with Python, Streamlit and Supabase, with a dark, mobile-friendly interface.

## Features

### 🏡 Home
- See a household overview or select a specific member's view.
- Check outstanding balances, upcoming reminders and shopping at a glance.
- Use quick actions for shopping and expenses, and shortcuts to relevant balance payments.
- Share shopping and balance summaries through WhatsApp.

### 🛒 Shared shopping list
- Add items with an optional quantity; no need to specify who added them.
- Mark items **Bought ✓**, undo a purchase or delete an item.
- Unbought items remain on the list across weeks.
- Share **only outstanding items** through WhatsApp.

### 💷 Shared expenses
- Record the item or purpose, amount, date and person who paid.
- Choose which household members share the cost.
- Calculate equal shares automatically and browse expenses by week.
- Amounts are stored and calculated in integer pence to avoid floating-point errors.

### ⚖️ Balances and repayments
- Show each person's outstanding balance and recommended transfers.
- Carry unpaid balances forward across weeks; choosing a week only changes the activity view.
- Record full or partial payments **after the recipient confirms receipt**.
- Keep a history of confirmed payments and share balances via WhatsApp.
- Download an **all-time household statement** as PDF or CSV, including expenses, confirmed payments and outstanding amounts.

> **Rounding note:** To give everyone the same displayed share, a £20.00 expense split three ways becomes £6.67 each. The small rounding difference is absorbed into the settlement calculation.

### 📅 Reminders and calendar
- Add household reminders, chores and events with dates, optional times and notes.
- Review upcoming events on Home or in Reminders.
- Delete events and download a calendar in **.ics** format for import into calendar apps.

### 📱 Mobile-friendly access
- Dark-themed responsive Streamlit app with navigation shortcuts.
- Optional GitHub Pages home-screen launcher in `docs/`, which embeds the public Streamlit app.
- Install the launcher on iPhone or Android using the instructions in [docs/SETUP.md](docs/SETUP.md).
- The launcher is **not an offline version** of the app: household data still comes from the online Streamlit/Supabase deployment.

## Technology

- **Python** — application logic and balance calculations
- **Streamlit** — interactive web interface
- **Supabase** — shared household database
- **ReportLab** — downloadable PDF statements
- **GitHub Pages** — optional mobile home-screen launcher

## Run locally

1. Clone the repository:

   ```bash
   git clone https://github.com/RAMEY031116/district-11.git
   cd district-11
   ```

2. Install dependencies (Python 3.10+ recommended):

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` with your existing Supabase project's credentials:

   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
   SUPABASE_KEY = "YOUR_SUPABASE_KEY"
   ```

   **Never commit real keys or `secrets.toml` to GitHub.** Keep a server-side key secret and restrict access appropriately. The app expects an existing Supabase schema; database setup SQL is not included in this repository.

4. Start the app:

   ```bash
   streamlit run app.py
   ```

The application reads and writes household records in Supabase. Its database code currently looks for a household named `District 11` and ensures its three configured members exist. To repurpose it for a different household, review that setup in `db.py`.

## Mobile home-screen launcher

The optional launcher lives in `docs/`. Configure GitHub Pages to deploy **main /docs**, then follow [the home-screen installation guide](docs/SETUP.md). This launcher embeds the existing public Streamlit deployment; it does not replace the Streamlit server or Supabase database.

## Tests

The repository includes a navigation-focused Streamlit test script:

```bash
python test_navigation.py
```

Tests are not a substitute for verifying the live Supabase connection or testing installation on physical phones.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit pages, user interface and workflows |
| `db.py` | Supabase access and household records |
| `calculations.py` | Equal splits, balances and suggested transfers |
| `statements.py` | All-time PDF/CSV statement generation |
| `test_navigation.py` | Navigation and payment interaction tests |
| `requirements.txt` | Python dependencies |
| `docs/` | GitHub Pages mobile launcher and setup instructions |

## How settlements work

Expenses accumulate in a shared ledger. Each member's balance reflects what they paid, their shares of expenses and **confirmed** payments. Balances do **not** reset at the start of a new week. A recipient must confirm receiving a payment before it is recorded, and any unpaid remainder stays outstanding.

---

**District 11 — one place to run a shared home.**
