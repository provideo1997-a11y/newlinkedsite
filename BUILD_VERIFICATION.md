# Build verification

## Implemented and locally checked

- The intake form uses a normal browser POST. JavaScript does not intercept submission or run an AJAX retry loop.
- The recurring visible arithmetic challenge has been removed; there is no human-answer field or challenge prompt in the intake UI. Flask-WTF CSRF, a signed per-form idempotency reference, a hidden honeypot, server-side validation and rate limiting remain.
- Optional phone, incident-date, account-handle and evidence fields safely accept blank submissions.
- Expired CSRF submissions re-render the same form with visitor-entered values preserved, a fresh CSRF token and the signed case reference preserved when its signature remains valid.
- A successful submission commits the case and advisory triage report before a 303 redirect to the separate signed case-ready page.
- The case-ready page retrieves the saved case and exposes exactly one WhatsApp link. The message is generated from the saved record and includes requester and incident information, original narrative, risk indicators and the advisory triage report.
- The hand-off token contains only the case reference and expires after 24 hours.
- Legacy databases receive a unique case-reference index migration; duplicate existing references stop startup with a clear error instead of disabling idempotency.

## Local checks completed

- `pytest -q`: **54 passed**.
- Python compilation: `app.py`, `security_utils.py`, `whatsapp_utils.py`.
- JavaScript syntax: `node --check static/js/app.js`.
- Jinja parsing: all 10 templates.
- YAML parsing: `render.yaml`.
- ZIP integrity and SHA-256 checked after packaging.

## Verification boundary

This environment does not have Flask, Flask-WTF, Flask-SQLAlchemy or Flask-Limiter installed, and package-index access is unavailable. Therefore a full Flask test-client POST, live Render PostgreSQL transaction and real WhatsApp app launch/send could not be executed here. Perform one dummy submission after deployment before accepting real customer records.
