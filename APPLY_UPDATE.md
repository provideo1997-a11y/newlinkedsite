# Apply the YAKUZA case-token recovery repair

1. Back up your current repository and database.
2. Extract this archive directly into the repository root.
3. Replace the project source files. Preserve `.git/`, `.env`, database files, backups and private uploads.
4. Review staged changes; do not commit secrets or database files.
5. Commit and push to the branch connected to your existing Render service.
6. Wait for deployment to finish. Confirm `/health/db` is healthy.
7. Open the contact form in a fresh private/incognito tab and submit one dummy case.

## What changed in this repair
The previous route-level expired-case-token response omitted the recovery code and fresh CSRF token expected by the JavaScript. The browser therefore kept stale hidden form values and repeated the same error. This build returns a complete refresh response, updates the visible challenge in place, and retries automatically when the old signed challenge can safely be renewed without changing its answer.

## Render settings
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Root directory: blank when `app.py` is at the repository root.
- Health check: `/health`

Keep `SECRET_KEY` stable across deploys and identical across all instances/workers. Keep `DATABASE_URL` and `WHATSAPP_NUMBER` in Render Environment, not in Git.

See `FINAL_DEPLOYMENT_DIAGNOSTICS.md` for the safe staging test.
