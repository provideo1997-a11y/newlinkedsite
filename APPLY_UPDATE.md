# Apply YAKUZA v9 to the existing GitHub repository

This archive is a full project-root replacement. It contains `app.py`, `requirements.txt`, `render.yaml`, templates, static assets, tests and documentation at the ZIP root.

## Safe replacement procedure

1. Make a local copy of the current repository and take a verified database backup before changing production code.
2. Open your existing local clone of `provideo1997-a11y/newlinkedsite`. Confirm you are on the same branch that the existing Render service deploys.
3. Keep the repository's `.git/` directory. Do not delete it. Do not include or overwrite `.env`, `instance/`, SQLite databases, backups, or private uploads.
4. Remove the old tracked project source files from the working tree (leaving `.git/` and ignored local secret/data files untouched), then extract **all contents of this ZIP** into the repository root. The ZIP has no enclosing project folder.
5. Check that `app.py`, `requirements.txt`, `render.yaml`, `templates/`, `static/`, and `tests/` are at the repository root.
6. Review `git status --short` and confirm no `.env`, database, backup, unrelated file, or secret is staged. Run the checks below.
7. Run `./COMMIT_UPDATE.sh` (Git Bash/macOS/Linux) or `./COMMIT_UPDATE.ps1` (PowerShell). Review the staged summary; the script asks you to type `COMMIT` before creating the commit and pushing the current branch. Confirm that this branch is the existing Render deployment branch. Do not force-push.

## Local checks

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
node --check static/js/app.js
pytest -q
```

The tests in this package validate translation catalogs, WhatsApp/database URL helpers, CSV safety, the UI copy catalog, and dashboard/report template hooks. Run the app locally with a disposable SQLite database and dummy admin credentials before deploying.

## Render settings

Keep your existing Render Web Service, repository, branch and environment variables. The expected settings are:

- Root Directory: blank when the project files are in repository root
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Health Check Path: `/health`

Do not create a second Render service from `render.yaml`. Preserve the existing `DATABASE_URL`; back it up and verify it points to the intended database before deployment. Do not set `RESET_ADMIN_PASSWORD=1` unless deliberately rotating the admin password for one deployment.

## Checks after deployment

1. `GET /health` returns HTTP 200 and the JSON status response.
2. Submit one disposable test case and confirm it is saved exactly once.
3. Check that the admin login, dashboard search/status filters, case report, status update and CSV export work. The dashboard filters only the 250 most recent server-rendered rows; CSV export remains the complete export.
4. Test copy-reference and print actions in an HTTPS browser.
5. Test all 11 admin locales, including Arabic RTL and Tunisian Arabic.
6. Test WhatsApp using a controlled number before enabling customer hand-off.
7. Confirm the test case is in the intended durable database before accepting real submissions.

## Verification boundary

This package was validated with Python compilation, JavaScript syntax checking, pytest, Jinja template parsing/rendering and YAML parsing in the build environment. The build environment could not install Flask dependencies or reach your GitHub/Render project, so a full Flask startup, live database migration, real browser/assistive-technology session, live WhatsApp hand-off and production deployment were not verified here.
