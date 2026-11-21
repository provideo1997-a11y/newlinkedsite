# Final deployment and submission diagnostics

Use this after replacing the application files and deploying the commit connected to the existing Render service.

## 1. Confirm the live application is running

Open `/health` on the deployed hostname. A 200 response confirms that the Flask service is responding; it does not prove that the database is available.

## 2. Confirm database reachability

Open `/health/db`. The route performs `SELECT 1` and intentionally reveals no database URL or credentials.

- HTTP 200 / `database: reachable`: basic database connectivity works.
- HTTP 503 / `database: unavailable`: inspect database status, active/expiry state, same-region networking, the current `DATABASE_URL`, and Render logs.

The app needs a working database at startup because it initializes/migrates the case tables. If startup fails before routes are served, inspect the Render deploy logs rather than the browser spinner.

## 3. Read a failed submission reference

When the POST reaches the app but cannot complete, the browser shows a support reference. Search Render Logs for `intake_failure`, then match the reference.

| Logged stage | What it points to |
|---|---|
| `idempotency_lookup` | Database connection/query before creating a new case. |
| `case_prepare` | Application-side case construction. |
| `database_flush` | Database insert/constraint/flush. |
| `whatsapp_message_build` | Destination validation or draft construction. |
| `database_commit` | Final transaction commit. |

Only the support ID, generated case reference, phase, exception type and elapsed time are logged. Form content, name, email, phone, evidence links and WhatsApp text are not logged.

If there is no matching application log, look at Render's service/deploy logs and browser Network panel. It may be a cold start, a platform-level 502/503, stale deployment, or request not reaching Flask.

## 4. One-button transaction behavior

The intake POST uses a signed per-form reference with a one-hour validity. Startup creates a unique database index for case references if an older table does not already enforce it. The migration checks for pre-existing duplicate non-null references and fails clearly if they exist. The server checks for an already committed case with the signed reference before re-validating the arithmetic answer, so a retry after a lost response hands off the existing case instead of inserting a duplicate. The unique index and recovery lookup handle simultaneous duplicate requests.

PostgreSQL connection attempts, pool checkout, lock waits and statements have explicit bounds. SQLite's lock wait is bounded. The browser waits up to 120 seconds and displays progress/error text; after a timeout the same form token is retained for safe retry.

## 5. WhatsApp behavior

The case is committed first. The server then provides a `wa.me` URL containing the case reference, requester contact details, incident metadata, narrative and advisory triage report. The client only permits an HTTPS `wa.me` destination with an 8–15 digit phone path, and navigates the current tab. The background fetch refuses redirects so it cannot accidentally follow an external redirect without changing the visible page.

WhatsApp itself still requires the visitor to press Send. This is not an official Business API integration and cannot confirm delivery.

## 6. Render Free behavior and data durability

Free web services can sleep after 15 minutes idle and take around one minute to wake. Free local filesystems are ephemeral. Free Render Postgres databases expire after 30 days. Keep real customer cases only in a durable database with backups and use an always-on plan before production use.
