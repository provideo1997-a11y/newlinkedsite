# Internal technical review — YAKUZA case platform

**Build scope:** public marketing site, structured complaint intake, protected case operations, multilingual UI and WhatsApp hand-off.

## Delivered
- Unique human-readable case reference for each accepted submission.
- Structured intake: contact, platform, account handle, incident date, category, urgency, narrative and optional HTTPS evidence link.
- Server-side validation, CSRF, per-IP rate limits, honeypot and session-bound arithmetic human check.
- Submission persisted before WhatsApp hand-off; prefilled WhatsApp message includes case reference and a short summary for the visitor to review/send.
- Private dashboard metrics, individual case report, status workflow and authenticated CSV export.
- Advisory triage report with transparent matched indicators and safe next-step guidance.
- Arabic RTL plus Arabic/Tunisian locale selector; existing language set retained.
- Additive schema migration for existing `inquiry` tables; PostgreSQL support retained.

## Risk review model
The current rules flag selected message patterns (credential requests, guaranteed-recovery claims and off-platform payment pressure). The displayed score is a prioritization hint only. It cannot prove a scam, verify a person's identity, authenticate evidence, or replace a human investigator. False positives and false negatives are expected. No external identity, sanctions, phone reputation or platform API checks are performed.

## Deployment requirements
- Python 3.12; `pip install -r requirements.txt`; `gunicorn --workers 1 --threads 4 --timeout 60 app:app`.
- Render environment: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` (14+ characters), `COOKIE_SECURE=1`, `ADMIN_URL_PREFIX=/private-inbox`, `WHATSAPP_NUMBER` (digits only), and a managed PostgreSQL `DATABASE_URL` for durable production data.
- Admin sign-in: `/private-inbox/login`; dashboard: `/private-inbox`.

## Production readiness review
**Good baseline:** CSRF, password hashing, rate limiting, session cookie flags, security headers, admin no-cache/no-index, authenticated export and input limits.

**Before real customer use:** connect managed PostgreSQL and automated backups; rotate any previously exposed admin password and secret; confirm `ADMIN_URL_PREFIX` is exactly `/private-inbox`; add email verification and a privacy/retention workflow; consider Cloudflare Turnstile or hCaptcha for stronger bot resistance; add audit logs, MFA, alerting, attachment quarantine/scanning and role-based access if the team grows. Do not collect passwords, OTPs, recovery keys, payment credentials or unnecessary identity documents.

**Limitations:** no account restoration automation, no platform affiliation, no guaranteed outcomes, no autonomous scam verdict, and WhatsApp replies are not synchronized into the case database.
