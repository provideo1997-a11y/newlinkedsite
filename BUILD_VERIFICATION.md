# Build verification — final reliability repair

Validation performed against this source tree:

- `pytest -q`: 42 tests passed.
- Python `compileall`: passed for `app.py`, `security_utils.py`, and `whatsapp_utils.py`.
- Python AST parsing for all project `.py` files: passed.
- `node --check static/js/app.js`: passed.
- Jinja syntax parsing for every HTML template: passed (9 templates).
- `render.yaml` parsed successfully as YAML.
- `bash -n COMMIT_UPDATE.sh`: passed.
- Actual SQLAlchemy SQLite connection smoke test (`SELECT 1`) using the configured bounded engine options: passed; legacy-table unique-index migration and duplicate-blocking behavior: passed. The full Flask app itself was not started because Flask, Flask-SQLAlchemy and related Flask dependencies were unavailable in this execution environment.
- ZIP CRC/integrity and SHA-256: verified after packaging.

## Changes specifically targeting the stuck submission

- Added PostgreSQL connect timeout, SQLAlchemy pool checkout timeout, server-side statement timeout and lock timeout.
- Added bounded SQLite lock wait.
- Added an explicit migration for the unique case-reference index on existing databases; startup detects duplicate pre-existing references and fails with a specific migration error rather than silently allowing duplicate cases.
- Added a protected, per-form signed reference. Retries after an uncertain network response reuse an already committed case.
- Kept exactly one public form submit control.
- Browser AJAX now explicitly refuses HTTP redirects (`redirect: error`). A successful JSON result must be received before the same tab is navigated to the server-generated `https://wa.me/` destination. This prevents a 303 from being followed invisibly inside `fetch`.
- Added progress states at 8 and 18 seconds and a 120-second client timeout; the decorative spinner stops after 8 seconds while accessible status text remains.
- Added a database diagnostic route at `/health/db`.
- Added support references and phase-level logs that omit submitted personally identifying information.

## Not verified in this execution environment

Flask, Flask-SQLAlchemy, Flask-WTF, Flask-Limiter, WTForms, psycopg and Gunicorn were not installed here; package-index/network access was unavailable. Therefore this environment could not launch the full Flask app or execute a Flask test-client submission against a live database. No live Render deploy, production database commit, Android/iOS/desktop WhatsApp launch, or actual message delivery was performed. The ZIP is source-validated, not a claim of live production verification.
