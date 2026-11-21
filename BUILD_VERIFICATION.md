# YAKUZA v12 build verification

Validation performed against the exact v12 source tree included in this archive:

- `pytest -q`: 32 tests passed.
- `python -m py_compile app.py security_utils.py whatsapp_utils.py`: passed.
- Python AST parsing: passed.
- `node --check static/js/app.js`: passed.
- Jinja syntax parsing: all 9 remaining HTML templates passed.
- Render YAML parse: passed; the web service health-check path is `/health`.
- `bash -n COMMIT_UPDATE.sh`: passed.
- ZIP integrity and SHA-256: verified after packaging.
- No new runtime dependency introduced.

## One-button WhatsApp behavior

1. The public case form contains one submit button labelled **Send to WhatsApp**; the contact method selection and receipt template are removed.
2. The visitor must explicitly consent to sharing the submitted case details through WhatsApp.
3. The server validates the destination, flushes the new case, builds the full prefilled message, and commits the case.
4. The server responds with HTTP 303 to the server-generated `https://wa.me/<number>?text=...` URL only after the commit succeeds.
5. A missing/invalid destination or database exception rolls back and prevents the redirect.
6. WhatsApp opens the prefilled draft. The visitor must inspect and press Send; the website cannot send from their account or verify final delivery via a standard click-to-chat link.

## Not verified in this environment

The execution environment did not have Flask/Flask-SQLAlchemy/Flask-WTF installed and package-index access was unavailable, so the Flask application was not started and database/route integration tests were not performed. Real Render deployment, production PostgreSQL commit behavior, WhatsApp application launch, and delivery to the destination number require staging/production testing.
