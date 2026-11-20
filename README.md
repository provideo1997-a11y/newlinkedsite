# YAKUZA | Private Operations Build

Private deployment notes. Do not publish credentials, customer reports, or environment exports.

## Deploy
- Runtime: Python 3.12
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Health: `/health`
- Root directory: blank when `app.py` and `requirements.txt` are at repository root.

## Required Render environment
`SECRET_KEY` (random 48+ byte secret), `ADMIN_USERNAME`, `ADMIN_PASSWORD` (minimum 14 characters), `COOKIE_SECURE=1`, `ADMIN_URL_PREFIX=/private-inbox`, `WHATSAPP_NUMBER` (international digits only), and `DATABASE_URL` (managed PostgreSQL recommended).

## Team access
Login: `/private-inbox/login`  
Dashboard: `/private-inbox`

## Case workflow
The public intake issues a unique `YKZ-YYMMDD-XXXXXX` reference, validates fields, applies CSRF/rate-limit/honeypot plus a simple human arithmetic check, and records a structured case. The team report includes requester details, incident context, priority, evidence link, status and advisory text indicators. CSV export is protected by admin authentication.

## Risk review limits
Keyword flags are triage prompts only. They do not identify a scammer, establish fraud, verify evidence authenticity, or replace a trained human review. False positives and false negatives are possible. Use official platform recovery channels; never request passwords, one-time codes, recovery keys, payment card data or remote access.

## WhatsApp
After the case is stored, the visitor can open WhatsApp with a prepared summary and must review and send it themselves. WhatsApp conversations are handled by WhatsApp and are not imported into this inbox automatically.

## Data protection
Use a private GitHub repository and managed PostgreSQL with backups for real cases. Render's ephemeral filesystem is not durable storage. Restrict dashboard access, rotate credentials if exposed, set a retention policy, and do not collect unnecessary identity documents. This build is an intake and case-management tool, not a guarantee of account recovery or a certified fraud-detection system.

## One-time admin password rotation
If the existing admin password was exposed, set `RESET_ADMIN_PASSWORD=1` in Render alongside the new `ADMIN_PASSWORD` (14+ characters), deploy once, then remove `RESET_ADMIN_PASSWORD` and deploy again. Existing admin hashes are otherwise not overwritten on every restart.
