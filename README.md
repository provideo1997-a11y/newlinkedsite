# YAKUZA — Private Case Desk

A Flask-based digital-risk intake and private case-management portal. It collects and organizes reports; it is not a managed investigation service, platform recovery provider, or guarantee of account recovery.

## Local development

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env and set local values
python app.py
```

Do not commit `.env`, credentials, customer data, SQLite databases, uploads, or backups.

## Case intake — two distinct pages

The public workflow deliberately uses ordinary HTML forms and Post/Redirect/Get. The intake page does not intercept the submit with JavaScript or use an AJAX/CSRF retry loop.

1. **Page 1 — Create secure case.** The visitor fills the form and gives explicit authorization and WhatsApp data-sharing consent. Flask-WTF validates the CSRF token; the route validates a signed per-form reference used for duplicate-safe retries.
2. **Save first.** The server validates `WHATSAPP_NUMBER`, prepares the complete case and advisory triage report, commits the database transaction, then responds with HTTP 303 to the second page. Retried submissions with the same signed case reference reuse the already-saved case and do not create duplicates.
3. **Page 2 — Case saved.** A signed, expiring hand-off token (case reference only; no personal data in the token) loads the saved case. The page displays the reference and a concise summary.
4. **Send to WhatsApp.** The second page has exactly one WhatsApp action. Clicking it opens `https://wa.me/<international-number>?text=<complete-report>` with requester details, incident details, original description, risk indicators and the generated advisory triage report already filled in.
5. **Visitor presses Send.** WhatsApp click-to-chat does not send automatically and does not notify the website that a message was delivered. The visitor must review and press Send inside WhatsApp.

There is no hidden background redirect and no client-side submission fetch. The visible arithmetic challenge has been removed because it repeatedly blocked otherwise valid submissions. Intake protection uses Flask-WTF CSRF, server-side validation, a honeypot, rate limiting and a signed per-form case reference. If the CSRF session expires, the server re-renders the same form, preserves submitted values, renews the hidden CSRF token and retains the case reference when its signature remains valid.

The `/case/ready/<token>` page token is signed and expires after 24 hours. The route fetches the saved record server-side and builds the WhatsApp URL from the saved record; it does not accept a user-supplied WhatsApp destination.

## Reliability and security

- Signed per-form case references plus a unique database index provide duplicate-safe retries, including simultaneous submissions.
- PostgreSQL connection, pool, lock and statement waits are bounded; SQLite lock waits are bounded too.
- Legacy databases receive an additive unique-index migration. Startup stops with a clear message if duplicate non-null legacy case references prevent that index.
- Explicit WhatsApp-sharing consent is required before case creation.
- The WhatsApp destination is validated and normalized to international digits-only form. Keep the real number in Render Environment, not in source code.
- The full report is generated from the saved database record. User text is treated as untrusted data and clearly delimited in the message.
- CSRF protection, server-side validation, a honeypot, rate limiting, request-size limit, secure cookie options, security headers, admin session checks and protected CSV export remain enabled.
- CSV formula-like values are neutralized before export.
- Application logs record failure stage, exception type and a support reference without logging submitted PII.

## Render deployment

When `app.py` is at repository root:

| Setting | Value |
|---|---|
| Root Directory | Blank |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn --workers 1 --threads 4 --timeout 60 app:app` |
| Health path | `/health` |
| Database health path | `/health/db` |

Environment variables:

| Key | Value / rule |
|---|---|
| `SECRET_KEY` | Long random secret; keep stable across deploys and all workers. Do not rotate it during a normal deploy. |
| `ADMIN_USERNAME` | Private administrator username. |
| `ADMIN_PASSWORD` | Unique 16+ character password when creating/resetting the admin. |
| `COOKIE_SECURE` | `1` on HTTPS Render; `0` only for local HTTP development. |
| `ADMIN_URL_PREFIX` | `/private-inbox` |
| `WHATSAPP_NUMBER` | Defaults to `4917642484892`; override only if you use a different WhatsApp destination. International digits only, no `+`, spaces, `00`, or domestic trunk zero. |
| `DATABASE_URL` | Reachable persistent PostgreSQL URL. Do not use local SQLite for permanent live records. |
| `INTAKE_RATE_LIMIT` | `30 per hour` by default. |
| `RATELIMIT_STORAGE_URI` | `memory://` only for a single-instance demo; use shared Redis-compatible storage when scaling. |

The application converts Render `postgres://` and `postgresql://` connection URLs to psycopg 3. Do not commit a real production connection string.

### Database diagnostics

Open `https://YOUR-SERVICE.onrender.com/health/db` after deployment:

- HTTP 200 with `{"status":"ok","database":"reachable"}` means the application can execute `SELECT 1`.
- HTTP 503 with `{"status":"error","database":"unavailable"}` means the database is not reachable or is not accepting queries.

If a submission fails, keep the displayed support reference and search Render application logs for `intake_failure` plus that reference. The `stage` value identifies duplicate lookup, database flush, WhatsApp message construction or commit. Logs intentionally omit case contents.

## Render Free limitations

Render Free web services sleep after 15 minutes without inbound traffic; the first request can take about a minute to wake. The local filesystem is ephemeral, so SQLite data is not durable. Free PostgreSQL expires after 30 days and does not include backups. Do not use free-tier storage for permanent customer case records. Use a persistent managed PostgreSQL database with backups and an always-on service before accepting real reports. See `RENDER_FREE_LIMITS.md`.

## Admin

- Login: `/private-inbox/login` (legacy `/private-inbox/logina` remains supported).
- Dashboard: `/private-inbox`.
- Case details, status updates and CSV export require an authenticated admin session and CSRF protection.
- An obscure admin URL is not an authentication control.

## Application behavior and language support

- Default intake limit is 30 submissions per hour per client IP; general app limits also apply.
- Risk indicators are advisory and are not fraud determinations.
- Dashboard search/filter applies to the 250 most recent rows loaded; CSV export covers all stored rows.
- Admin/dashboard and primary intake flow are bundled for English, French, Arabic, Tunisian Arabic, Spanish, German, Italian, Portuguese, Turkish, Simplified Chinese and Japanese.

## Data and privacy

Collect only information necessary to assess the report. Never request passwords, one-time codes, recovery keys, session cookies, payment credentials or unnecessary identity documents. Publish a privacy notice describing purpose, lawful basis, retention, contact details and data-subject rights before accepting real customer records. Restrict exports and protect backups.

See `TWO_STEP_WHATSAPP_FLOW.md`, `FINAL_DEPLOYMENT_DIAGNOSTICS.md`, `SECURITY_ARCHITECTURE.md`, `TECHNICAL_REVIEW.md`, and `UI_UX_REVIEW.md`.


### Intake diagnostics

Open `/health/intake` to check that the configured database is reachable and `WHATSAPP_NUMBER` has a valid international number shape. It does not verify that the number is registered on WhatsApp. On a failed submission, use the support reference displayed on the error page and search Render logs for `intake_request_received`, `intake_request_completed`, or `unhandled_request_failure`.
