# YAKUZA — Private Case Desk

A Flask-based digital-risk intake and private case-management portal. This is software for collecting and organizing reports; it is not a managed investigation service, platform recovery provider, or guarantee of account recovery.

## Local development

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env and set local values before running
python app.py
```

Do not commit `.env`, credentials, customer data, SQLite databases, uploads, or backups.

## One-button WhatsApp case intake and reliability controls

The public form has exactly one submit action: **Send to WhatsApp**. There is no contact-method selection, separate receipt page, second WhatsApp button, or alternative delivery path.

The single action follows this order:

1. Browser posts the form and CSRF token to the same-origin `/contact` endpoint.
2. Server validates the form, signed per-form case token, authorization, explicit WhatsApp data-sharing consent, human challenge, and configured destination number.
3. Server creates the case and triage report, builds the WhatsApp draft, flushes and commits the database transaction.
4. Only after successful commit does the server return the prefilled WhatsApp destination. JavaScript validates that the destination is `https://wa.me/<digits>` and opens it in the same tab. Without JavaScript, the normal form receives a `303` redirect after commit.

The request has bounded PostgreSQL connection, pool, lock, and statement waits; SQLite lock waits are also bounded. A 120-second browser timeout covers Render Free cold-start behavior. Each form has a signed, time-limited case reference, and startup ensures the database has a unique index for that reference (including older tables where `create_all` would not add a new constraint). Retry of the same form after a network timeout reuses the original committed case instead of creating a duplicate. If old data already contains duplicate non-null case references, startup stops with an explicit migration error so the records can be reconciled safely. A `support_reference` is returned for server-side failures, and application logs record the failing stage without logging submitted PII.

The browser fetch is configured not to follow redirects in the background. A successful JSON response is required before the page navigates to WhatsApp. An unexpected redirect or non-JSON response becomes a visible error instead of disappearing inside a fetch request.

**WhatsApp limitation:** a `wa.me` click-to-chat link can open a chat with prefilled text, but cannot press Send from the visitor's account or confirm delivery. The visitor must review and press Send inside WhatsApp. The message contains the case details and triage report, so the form requires explicit consent. The submitted case is already saved before WhatsApp opens.

## Deployment on Render

- Root Directory: blank when `app.py` is in the repository root.
- Runtime: Python 3.12.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Basic health path: `/health`
- Database diagnostic path: `/health/db` (returns 200 only when the database answers `SELECT 1`).

Required Render environment variables:

| Key | Value / rule |
|---|---|
| `SECRET_KEY` | Long random secret; keep stable across deploys and rotate if exposed. |
| `ADMIN_USERNAME` | Your private admin username. |
| `ADMIN_PASSWORD` | Unique password of at least 16 characters when first creating/resetting admin. |
| `COOKIE_SECURE` | `1` |
| `ADMIN_URL_PREFIX` | `/private-inbox` |
| `WHATSAPP_NUMBER` | International digits only: country code followed by subscriber number, without `+`, spaces, `00`, or a domestic trunk zero. Keep the real number in Render Environment only. |
| `DATABASE_URL` | A reachable PostgreSQL connection URL. Do not rely on SQLite for real case records. |
| `INTAKE_RATE_LIMIT` | `30 per hour` by default; tune deliberately. |
| `RATELIMIT_STORAGE_URI` | `memory://` only for the single-instance demo; use shared Redis-compatible storage when scaling. |

The application converts `postgres://` and `postgresql://` URLs to the installed psycopg 3 driver. Make sure the database is active, the database URL is current, and the web service and database can communicate in Render. Never commit a real production connection string.

### Submission troubleshooting

After deployment, open `https://YOUR-SERVICE.onrender.com/health/db`:

- `200` with `{"status":"ok","database":"reachable"}` means the application can execute a trivial database query.
- `503` with `{"status":"error","database":"unavailable"}` means the database is not reachable or is not accepting queries. Check Render's database status, expiration, region, URL, and logs.

When a form submission fails, the page shows a support reference. In Render Logs, search for `intake_failure` and that support reference. The `stage` field identifies whether it failed during the duplicate lookup, database flush, WhatsApp message creation, or database commit. These logs intentionally omit the submitted case contents.

If there is no matching application log, inspect the Render service/deploy logs and confirm the newest commit is deployed. A Render Free web service may be asleep or starting; see `RENDER_FREE_LIMITS.md`.

## Render persistence and availability limits

Render Free web services sleep after 15 minutes without inbound traffic, and the next request can take about a minute to wake. Their local filesystem is ephemeral, so SQLite data is not durable. Render Free PostgreSQL expires after 30 days and has no backups. Do not use this setup for permanent customer case storage. Use an active managed PostgreSQL database with backups and a paid always-on web service before collecting real reports. See `RENDER_FREE_LIMITS.md`.

## Admin

- Login: `/private-inbox/login` (the legacy `/private-inbox/logina` route remains supported).
- Dashboard: `/private-inbox`
- Case details, status changes and CSV export require an authenticated admin session and CSRF protection.
- An obscure admin URL is not an authentication control.

## Application behavior

- Default intake limit is 30 submissions per hour per client IP; the general app limit is also applied.
- Case risk indicators are advisory and are not fraud determinations.
- The admin dashboard search/filter covers the 250 newest rows loaded on the page; CSV export covers all stored rows.
- Admin/dashboard translations are bundled for English, French, Arabic, Tunisian Arabic, Spanish, German, Italian, Portuguese, Turkish, Simplified Chinese and Japanese. Untranslated public intake copy in the four additional admin locales may fall back to English.

## Data and privacy

Collect only information needed to assess the report. Never request passwords, one-time codes, recovery keys, session cookies, payment credentials, or unnecessary identity documents. Publish a privacy notice describing purpose, lawful basis, retention, contact details and data-subject rights before accepting real customer records. Restrict exports and protect backups.

See `SECURITY_ARCHITECTURE.md`, `TECHNICAL_REVIEW.md`, `UI_UX_REVIEW.md`, and `FINAL_DEPLOYMENT_DIAGNOSTICS.md`.
