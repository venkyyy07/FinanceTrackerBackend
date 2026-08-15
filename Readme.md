# Tally — Personal Finance Tracker

A full personal finance tracker built with vanilla HTML, CSS, and JavaScript on the frontend, backed by a local Flask + SQLite server for authentication and data storage.

Designed with a "ledger / passbook" visual identity: serif display type, monospace tabular figures, stamp-style category markers, and soft ambient glow accents — rather than a generic dashboard template.

## Live Demo
[Add your GitHub Pages link here after deployment — note: GitHub Pages only serves the static frontend, so the Flask backend will need to be hosted separately for a live demo to fully work]

## Features
- **Authentication** — sign in / sign up against the Flask backend, with the session persisted in the browser so a refresh doesn't log you out
- **Dashboard** — current balance, income/expense totals, this month's activity, category breakdown chart, recent entries
- **Transactions** — full ledger with add, edit, and delete for both income and expense entries; search, filter by type/category, and sort
- **Profile** — editable name, currency, and monthly budget goal behind an **Edit profile** toggle (fields are read-only until you choose to edit), plus account stats (member since, total entries, net balance)
- Password visibility toggle (eye icon) on the sign-in and sign-up forms
- Sidebar navigation between views (single-page app, no reload)
- Dark mode toggle with persisted preference
- Fully responsive layout (sidebar collapses to a top bar on mobile)
- Active view and theme preference persist across refresh via `localStorage`; transactions and profile data persist server-side via the Flask + SQLite backend

## Tech Stack
- **HTML5** — semantic structure, single-page view switching
- **CSS3** — custom properties (variables) for theming, CSS Grid & Flexbox for layout, media queries for responsiveness
- **JavaScript (ES6+)** — DOM manipulation, array methods (`filter`, `reduce`, `sort`, `map`), `fetch` for API calls, `localStorage` for session/UI state
- **Flask + SQLite** — local backend serving auth and CRUD endpoints for transactions and profile data (runs at `127.0.0.1:5000`)
- **Chart.js** — category spend visualization (via CDN)
- **Google Fonts** — Fraunces (display serif), Inter (UI text), IBM Plex Mono (tabular figures)

## How to Run
1. Clone this repository
2. Start the Flask backend so it's listening on `127.0.0.1:5000` (see your backend's own setup instructions — install its dependencies and run it, e.g. `python app.py`)
3. Open `index.html` directly in a browser, or serve it with a local server (e.g. VS Code Live Server)
4. Sign up for an account, then sign in — no separate build step needed for the frontend

## Project Structure
```
tally/
├── index.html
├── Style.css
├── App.js
└── README.md
```

## Technical Highlights
- Transactions and profile data live in Flask + SQLite and are fetched per-user (`?user_id=...`) on login; the frontend re-renders from a single `renderAll()` function after every change, keeping one clear render path.
- Income and expense entries share one data model (`type: "income" | "expense"`), so totals, filtering, and the balance calculation are all derived from the same array rather than duplicated logic.
- Filtering, searching, and sorting are computed on read (`getVisibleEntries()`) rather than mutating the underlying data, keeping the source of truth intact.
- Edit reuses the same modal/form as Add — the form is populated from the selected entry and the submit handler branches on whether an `editingId` is set.
- The active view (dashboard/transactions/profile) is tracked explicitly and re-asserted after any add/edit/delete, so saving an entry never silently kicks you back to the dashboard.
- Theming uses CSS custom properties toggled via a `data-theme` attribute, avoiding duplicated stylesheets for light/dark mode.

## Possible Improvements
- Export data to CSV
- Multi-month trend view
- Password reset flow
- Recurring transactions
- Deploy the Flask backend somewhere persistent so the live demo works end-to-end

## Screenshot
_Add a screenshot of the running app here._