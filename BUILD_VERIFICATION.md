# YAKUZA v11 build verification

Validation performed against the exact source tree included in this archive:

- `pytest -q`: **32 tests passed**, including WhatsApp destination normalization, full draft payload, URL encoding, invalid-number rejection, required sharing consent, database-commit-before-draft ordering, explicit-button-only hand-off, translation catalogs, and receipt security attributes.
- `python -m compileall -q .`: passed.
- Python AST parsing for project Python files: passed.
- `node --check static/js/app.js`: passed.
- Jinja syntax parsing: all 10 HTML templates parsed successfully.
- Render YAML syntax and health-check configuration parsed successfully.
- Shell commit helper syntax: `bash -n COMMIT_UPDATE.sh` passed.
- No new runtime dependency was introduced. The WhatsApp message and URL helper use the Python standard library.
- Release hygiene: `.env`, instance databases, backups, Python caches, pytest caches, and temporary previews are excluded from the archive.
- ZIP integrity and SHA-256 checksum were verified after packaging.

## WhatsApp behavior in v11

1. The visitor selects WhatsApp as the preferred contact method and separately consents to share the case details.
2. The server validates the input, builds the case reference and advisory triage report, and commits the case to the configured database.
3. If the database commit fails, the transaction is rolled back, an error is shown, and the visitor is not offered a WhatsApp hand-off.
4. After a successful commit, the receipt displays exactly one WhatsApp button with a direct `https://wa.me/<number>?text=...` link.
5. No script, timer, load handler, form submission handler, or page redirect opens WhatsApp automatically. WhatsApp opens only after the visitor clicks the button.
6. The message draft includes the case reference, requester details, incident fields, full description, advisory risk indicators, and generated triage report.
7. The visitor must inspect the draft and press Send in WhatsApp. A standard click-to-chat link cannot send automatically or tell the website whether the visitor completed the send.

## Environment requirement

Set `WHATSAPP_NUMBER` in Render → Web Service → Environment to the business destination in international digits-only format. For a German number, begin with `49` and omit `+`, `00`, spaces, and Germany's domestic trunk zero. Keep the production number in Render rather than committing it into public source. Redeploy after changing the value.

## Not performed in this environment

- Full Flask startup or live route test: Flask dependencies were not installed in this build environment.
- Live PostgreSQL transaction, migration, or production-database validation.
- Real mobile/desktop WhatsApp launch, account registration check, or actual message delivery. The number was validated for format only.
- Live Render deployment or GitHub commit/push.
- Independent penetration test, accessibility certification, or load test.

This archive is source-validated and unit-tested. It is not a claim that the live Render site or end-to-end WhatsApp delivery has been tested.
