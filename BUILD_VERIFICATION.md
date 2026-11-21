# Build verification — case-token recovery repair

## Root cause confirmed in the previous build
The `/contact` route had its own JSON error helper for an expired/invalid signed case token. It returned a replacement `case_token` and `human_question`, but did not return a machine-readable recovery code or a fresh Flask-WTF `csrf_token`. The browser only applied refreshed values when it saw `CSRF_TOKEN_REFRESHED`, so it kept posting the stale hidden case token and did not update the arithmetic prompt. The user repeatedly saw the token-renewal message without a working next step.

## Corrected behavior
- Route-level recovery now returns `CASE_TOKEN_REFRESHED`, a fresh CSRF token, a new/current case token, the visible arithmetic question, and an explicit retryability flag.
- Client code recognizes both CSRF and case-token recovery responses, updates the hidden fields and visible question, clears the old answer when a new challenge is required, and focuses the new answer field.
- Authentic case tokens older than one hour but younger than 24 hours are re-signed while preserving the case reference and arithmetic challenge, allowing the original submission to continue or be retried without creating a duplicate.
- Tokens with an invalid signature, a different signing secret, or an age beyond the grace window receive a genuinely new reference/challenge. The new challenge is rendered in place; no page reload is requested.
- The JavaScript cache key is bumped so the browser loads the corrected handler.

## Verification completed in this environment
- `pytest -q`: **51 passed**.
- `python -m py_compile app.py security_utils.py whatsapp_utils.py`: passed.
- Python AST parse: 12 project/test Python files passed.
- `node --check static/js/app.js`: passed.
- Jinja parse: all 9 templates passed.
- Regression tests exercise actual extracted ItsDangerous helper functions for (a) a valid but expired token preserving its reference and challenge, and (b) a token signed by an old secret producing a fresh challenge.
- ZIP contents and SHA-256 checksum verified after packaging.

## Not verified here
Flask, Flask-SQLAlchemy, Flask-WTF and Flask-Limiter are not installed in this build runtime, and package-index access is unavailable. Therefore a full Flask test-client submission against PostgreSQL, a live Render request, and WhatsApp launch/send could not be run here. The application must be deployed to staging and tested with a dummy case before receiving real customer records.
