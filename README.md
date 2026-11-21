# YAKUZA — Private Case Desk

A Flask-based digital-risk intake and private case-management portal. This repository is a starter implementation, not a managed investigation service or a guarantee of account recovery.

## Local run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; configure values before running
python app.py
```

For production, set environment variables in Render. Do not commit `.env`, credentials, customer data, SQLite databases, or backups.


## WhatsApp and case-intake hand-off (v10)

When a visitor chooses WhatsApp, the server validates the separate WhatsApp-sharing consent, creates the case in the configured database, commits it, and only then renders the receipt page that opens the configured WhatsApp chat. The prefilled message includes the saved case reference, requester contact details, selected platform/category/priority, account handle, incident date, evidence URL, full user-submitted description, risk indicators, and generated triage report. The receipt page retains a manual WhatsApp link if automatic navigation is blocked.

**The visitor must still review the draft and press Send in WhatsApp.** A normal `wa.me` click-to-chat link cannot send messages automatically or tell the website whether the visitor completed the send. No WhatsApp Cloud API token or webhook is assumed.

Because the requested full message includes personal information, the page requires an explicit separate consent for WhatsApp sharing. The WhatsApp URL contains the message text, so it is exposed to the WhatsApp service and may remain in browser history. Do not include passwords, one-time codes, recovery keys, payment data, or unnecessary identity documents. If database persistence fails, the app does not open WhatsApp and displays a save error instead.

## UI release (v9)

This release keeps the existing Flask/Jinja, CSS and vanilla JavaScript stack and adds:
- A keyboard skip link, labelled landmarks, current-page navigation state, explicit focus-visible styles, and more legible muted text.
- A progressive loading overlay that is enabled only when JavaScript is available; users without JavaScript are not blocked by the loader.
- Dashboard search and status filters for the 250 newest rows already loaded on the page. Filtering is client-side and does not change server-side case access or the complete CSV export.
- Localized dashboard controls and accessibility labels in all 11 bundled admin locales.
- Case-reference copy feedback, report printing, and print-specific styles.
- Native browser form validation, a date input, and an accessible character-counter description.

No frontend framework or new runtime dependency was added. See `UI_UX_REVIEW.md` for the source-based UI review, shipped changes, performance considerations and future roadmap.

## Render deployment

- Root Directory: blank when the contents of this folder are at repository root.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Health Check Path: `/health`
- Runtime: Python 3.12

Required environment variables:
- `SECRET_KEY`: long random secret; rotate if exposed.
- `ADMIN_USERNAME`: unique admin username.
- `ADMIN_PASSWORD`: unique password with at least 16 characters.
- `COOKIE_SECURE=1`
- `ADMIN_URL_PREFIX=/private-inbox`
- `WHATSAPP_NUMBER`: international phone number. The code normalizes `0049...`, `+49...`, and `49...` into the `wa.me` format.
- `DATABASE_URL`: managed PostgreSQL connection string. Both `postgres://` and `postgresql://` are normalized to SQLAlchemy `postgresql+psycopg://` because the project installs psycopg 3.
- `INTAKE_RATE_LIMIT=30 per hour` (per client IP; the application-wide default is also 50 requests/hour).
- `RATELIMIT_STORAGE_URI=memory://` is process-local and resets when the service restarts. Keep one Render instance for this demo setting; use shared Redis-compatible storage before scaling.

### WhatsApp setup

In Render → your Web Service → Environment:
1. Add the key `WHATSAPP_NUMBER`.
2. Set its value to the full German international number in digits only: country code `49` followed by the subscriber number, without `+`, spaces, `00`, or the domestic trunk zero.
3. Save changes and redeploy.
4. Submit a controlled test case, select WhatsApp, and tick the separate WhatsApp data-sharing consent.
5. The case is committed first. The receipt page then opens WhatsApp with the full case details and generated triage report; the visitor reviews and taps Send. A manual fallback link remains visible on the receipt page.

Keep the real destination number in Render Environment only. Do not place private phone numbers in source files or commit them to Git.
### Database: critical limitation

SQLite on a Render web service is not durable. Render Free web services have an ephemeral filesystem, and Free Postgres databases expire after 30 days. A free service also spins down after 15 minutes idle and takes about a minute to wake. Therefore **a permanently available site with permanent case storage cannot be guaranteed on Render Free**. Use a paid managed Postgres database (or another durable PostgreSQL provider with backups) before accepting real case records. See `RENDER_FREE_LIMITS.md`.

## Admin

- Login: `/private-inbox/login`
- Dashboard: `/private-inbox`
- Case detail pages, status updates, and CSV export are protected by the admin session and CSRF protection.
- Keep the admin path obscure if desired, but it is not an authentication control. Password protection remains mandatory.
- If you intentionally need a one-time password reset for the existing admin user, set a new `ADMIN_PASSWORD` of at least 16 characters and `RESET_ADMIN_PASSWORD=1`, deploy once, then remove `RESET_ADMIN_PASSWORD` and redeploy. Do not leave this flag enabled.

## Intake behavior

- The old hard-coded `5 per hour` form limit is replaced by configurable `30 per hour` by default.
- A unique case reference is created and the record is committed before WhatsApp is opened. Full-message sharing requires separate consent; the final Send action remains manual in WhatsApp.
- Risk indicators are advisory and are not fraud determinations.
- The dashboard, case report, receipt, and triage labels are translated in 11 bundled locales, including Arabic RTL and Tunisian Arabic. The four additional admin locales (Portuguese, Turkish, Simplified Chinese, Japanese) use English fallback for untranslated public marketing/intake copy; they are not claimed as complete public-site translations.

## Data and privacy

Collect only what is necessary. Do not ask users for passwords, one-time codes, recovery keys, session cookies, payment credentials, or unnecessary identity documents. Publish a real privacy notice, contact address, lawful basis, retention period, and data-subject request process before collecting real customer data. Restrict CSV exports and store backups securely.

See:
- `SECURITY_ARCHITECTURE.md`
- `TECHNICAL_REVIEW.md`
- `RENDER_FREE_LIMITS.md`
