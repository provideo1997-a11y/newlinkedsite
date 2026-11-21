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


## Single-button WhatsApp case intake (v12)

The public intake form has exactly one delivery action: **Send to WhatsApp**. The visitor completes the form, checks the explicit WhatsApp data-sharing consent, and submits once. The server validates the configured destination, creates and commits the case, then responds with a `303` redirect to a prefilled `https://wa.me/` message containing the full case reference, requester and incident details, description, advisory indicators, and generated triage report. There is no contact-method choice, intermediate receipt page, second WhatsApp button, or fallback delivery option.

The visitor must review the draft and press **Send** inside WhatsApp. A standard `wa.me` link cannot send from the visitor's account or notify the website whether the send completed. The message URL contains the submitted personal information and is shared with the WhatsApp service; the form therefore requires explicit consent. If `WHATSAPP_NUMBER` is invalid/missing or the database transaction fails, the transaction is rolled back and the app does not redirect to WhatsApp.

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
4. Submit one controlled dummy case and tick the required WhatsApp data-sharing consent.
5. The single form submission saves the case and redirects directly to WhatsApp with the full case details and generated triage report prefilled. The visitor reviews the draft and taps Send.

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
- The dashboard, case report, and triage labels are translated in 11 bundled locales, including Arabic RTL and Tunisian Arabic. The four additional admin locales (Portuguese, Turkish, Simplified Chinese, Japanese) use English fallback for untranslated public marketing/intake copy; they are not claimed as complete public-site translations.

## Data and privacy

Collect only what is necessary. Do not ask users for passwords, one-time codes, recovery keys, session cookies, payment credentials, or unnecessary identity documents. Publish a real privacy notice, contact address, lawful basis, retention period, and data-subject request process before collecting real customer data. Restrict CSV exports and store backups securely.

See:
- `SECURITY_ARCHITECTURE.md`
- `TECHNICAL_REVIEW.md`
- `RENDER_FREE_LIMITS.md`
