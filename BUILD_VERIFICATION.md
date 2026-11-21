# YAKUZA v9 build verification

Validation performed against the source tree included in this archive:

- `pytest -q`: **18 tests passed** (security helpers, locale catalogs, UI translation coverage, shell semantics, dashboard filters, case-report actions and progressive loader rules).
- `python -m compileall -q .`: passed.
- `node --check static/js/app.js`: passed.
- Jinja parsing: all 10 HTML templates parsed successfully.
- Representative Jinja rendering: the public intake form, admin dashboard and case report rendered with fixture data; new form attributes and interactive hooks appeared in output.
- `render.yaml`: parsed successfully; `/health` and the Gunicorn start command were checked.
- Contrast spot checks: small muted text/placeholder colors were raised in the dark UI; final values are `#9aa6aa` / `#879198` on dark surfaces. This is a targeted contrast correction, not a complete WCAG audit.
- Commit helper: `bash -n COMMIT_UPDATE.sh` passed. The PowerShell helper is included but was not executed because PowerShell is unavailable in this environment.
- Dependency delta: no new runtime packages were introduced.
- Release hygiene: the ZIP excludes `.env`, instance database files, backups, browser previews and local caches.
- ZIP integrity and SHA-256 checksum: verified after archive creation.

Not performed in this environment:

- Full Flask application startup or route integration test. Flask dependencies were not preinstalled and the package index could not be reached from this environment.
- Live PostgreSQL connection or migration against the production database.
- Actual Render deployment, authenticated test against the live service, or GitHub commit/push.
- Real WhatsApp hand-off with the configured destination number.
- End-to-end interactive browser test or assistive-technology validation; the headless browser launch was blocked by the execution environment.
- Independent penetration test, accessibility certification, load test or Core Web Vitals measurement.

The archive is therefore a source-validated, commit-ready full replacement with focused UI regression tests. It is not a claim that a live production deployment has been verified.
