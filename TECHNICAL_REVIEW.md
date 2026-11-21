# Technical review — YAKUZA Private Case Desk

## Current implementation

- Flask public website, structured case intake and private case-management dashboard.
- Flask/Jinja templates, vanilla JavaScript and responsive CSS; no additional frontend runtime or CDN.
- Multilingual public and admin UI, including Arabic RTL and Tunisian Arabic.
- Admin dashboard, individual case report, status changes, protected CSV export, search and status filters.
- CSRF protection, server-side form validation, honeypot, rate limiting, request-size limit, secure cookie options, security headers and admin session checks.
- PostgreSQL URL normalization to psycopg 3; bounded database connection, pool, lock and statement waits.
- Additive legacy database migration and unique case-reference index for retry safety.
- WhatsApp international-number normalization and full saved-case message generation.

## Case submission architecture

The intake does not use an AJAX submission handler. It uses a standard HTML POST and Post/Redirect/Get:

1. GET `/contact` creates a signed per-form case reference.
2. POST `/contact` is validated by Flask-WTF CSRF, WTForms, signed case-reference verification, consent checks and WhatsApp destination validation.
3. The case and advisory triage report are inserted and committed to the database.
4. The server redirects with HTTP 303 to `/case/ready/<signed-token>`. The hand-off token is signed, contains only the case reference and expires after 24 hours.
5. The second page loads the saved record and exposes exactly one WhatsApp click-to-chat link containing the full prepared message.
6. The visitor reviews and presses Send in WhatsApp. The site cannot send through a visitor's personal WhatsApp account or confirm delivery without the WhatsApp Business Platform and an appropriate integration.

CSRF expiry re-renders the same form, preserves submitted fields and refreshes the hidden Flask-WTF token. The signed case reference is retained when still authentic. The visible arithmetic challenge and its retry failure mode have been removed; bot resistance uses CSRF, the honeypot and server-side rate limiting.

## Important limitations

- This source ZIP was created from the latest uploaded YAKUZA archive. The remote GitHub repository was not modified and Render was not deployed from this session.
- The current build container did not have Flask / Flask-WTF / Flask-SQLAlchemy installed and could not reach the package index. Full Flask test-client submission and live PostgreSQL integration were therefore not run here.
- No production penetration test, independent code audit, or real WhatsApp app delivery test was performed.
- Render Free cannot provide permanent uptime or durable case storage. Free PostgreSQL expires after 30 days; local files are ephemeral. See `RENDER_FREE_LIMITS.md`.
- `memory://` rate limiting is process-local and resets on restart. Use shared storage when scaling.
- Admin MFA, per-action append-only audit history, email verification, private file quarantine/scanning and formal retention automation remain additional production hardening work.

## Automated checks in this release

The release uses pytest tests for utility behavior, token helpers, source contracts, translations, CSV safety, duplicate-index migration and the two-step form/hand-off contract. Python compilation, JavaScript syntax and Jinja parse checks are also run during packaging. These checks do not substitute for a live Render smoke test with a dummy case.
