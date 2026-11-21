# YAKUZA v10 build verification

Validation performed against the exact source tree included in this archive:

- `pytest -q`: **27 tests passed**, including WhatsApp number normalization, complete draft payload, URL encoding, invalid-number rejection, required data-sharing consent, database-commit-before-handoff ordering, receipt fallback and privacy-header preservation.
- `python -m compileall -q .`: passed.
- `node --check static/js/app.js`: passed.
- Jinja syntax parsing: all 10 HTML templates parsed successfully.
- Render YAML syntax and required service settings parsed successfully.
- Source-level checks confirm the receipt uses a no-store response and `Referrer-Policy: no-referrer`.
- Shell commit helper syntax: `bash -n COMMIT_UPDATE.sh` passed.
- No new runtime Python dependency was introduced; `whatsapp_utils.py` uses Python standard-library URL encoding.
- Release hygiene: `.env`, instance databases, backups, Python caches, and local previews are excluded from the archive.
- ZIP integrity and SHA-256 checksum were verified after packaging.

## WhatsApp behavior now implemented

1. The user selects WhatsApp and separately consents to share the submitted case information.
2. The server validates the configured international destination number.
3. The Flask application generates the case reference, saves the complete user-entered narrative and incident fields, builds advisory triage text, and commits the record.
4. If the database commit fails, the transaction is rolled back, an error is shown, and no WhatsApp URL is generated.
5. After a successful commit, the receipt confirms the saved case and automatically navigates to a `wa.me` URL containing the full case summary and triage report. A visible manual link is available if auto-navigation is blocked.
6. The visitor still has to review and press Send in WhatsApp. A click-to-chat URL does not send a message and the website cannot observe that final action without a separate WhatsApp Business Platform/API webhook integration.

## Not performed in this environment

- Full Flask startup or live request/route integration test: Flask dependencies were not installed in the build environment, and the package index was unreachable.
- Live PostgreSQL test, migration, or validation against the production database.
- Real device/browser launch into WhatsApp, WhatsApp account registration check, or delivery test. The user-provided number is format-valid but account ownership/registration cannot be confirmed from the number alone.
- Live Render deployment or GitHub commit/push.
- Independent penetration test, accessibility certification, performance/load test, or production monitoring validation.

This archive is source-validated with focused regression tests. It is not a claim that the live service or real WhatsApp delivery has been tested.
