# Technical review — YAKUZA Private Case Desk

## Delivered in this build
- Flask public website and structured case intake.
- Multilingual public site and intake, including Arabic RTL and Tunisian Arabic.
- Admin dashboard, individual case report, status updates, and protected CSV export.
- Dashboard, case detail, receipt, and risk-triage interface translations for all bundled locales.
- Admin language choice is retained across successful login. Eleven admin locales are initialized safely; four additional admin locales use English fallback on untranslated public-site pages.
- Configurable intake rate limit; default raised from 5/hour to 30/hour.
- CSRF, server-side validation, honeypot, arithmetic challenge, request-size limit, secure cookie options, security headers, and admin session checks.
- WhatsApp number normalization for `0049...`, `+49...`, and digits-only international formats.
- WhatsApp prefilled message minimizes personal data and includes only the case reference.
- CSV formula-injection neutralization.
- Accurate dashboard totals beyond the latest 250 displayed records.
- PostgreSQL URL normalization to the installed psycopg 3 driver, and Render deployment configuration.

## Important limitations
- The uploaded project ZIP was inspected and modified. The remote GitHub repository was not changed; authenticated write access was not available in this session.
- No live Render deployment was triggered.
- No production penetration test, independent code audit, or live WhatsApp delivery test was performed.
- Free Render hosting cannot provide permanent uptime or durable case storage. Free Postgres expires after 30 days; local filesystem data is ephemeral. See `RENDER_FREE_LIMITS.md`.
- `memory://` rate limiting is process-local and resets on restart. The public intake endpoint has a configurable 30/hour IP limit, but the app-wide 50/hour default can also apply. This is acceptable for a one-instance demo only.
- Admin MFA, per-action audit logging, email verification, attachment quarantine, replay/idempotency protection for concurrent duplicate submissions, and formal retention automation remain production hardening work.

## Test status
Static syntax/structure and ZIP integrity checks should be run before release. A real deployment must also complete the manual end-to-end checklist in `FREE_HOSTING_AND_DOMAIN_GUIDE.md` and `SECURITY_ARCHITECTURE.md`.
