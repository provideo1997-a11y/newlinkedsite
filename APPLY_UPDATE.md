# Apply the final YAKUZA repair

1. Back up your existing database and repository.
2. Extract this archive directly into the repository root.
3. Replace the source files. Preserve `.git/`, `.env`, database files, backups, and private uploads.
4. Review the staged changes and ensure no secrets or database files are added.
5. Commit and push to the branch connected to your existing Render service.
6. Wait for Render to finish deploying, then open `/health/db`.
7. Test with a dummy submission from a private/incognito window.

## Render settings
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Root directory: blank when `app.py` is at repository root.
- Health check: `/health`

## Required environment values
Keep your existing `SECRET_KEY`, `ADMIN_PASSWORD`, `ADMIN_USERNAME`, and `DATABASE_URL`. Ensure `SECRET_KEY` is stable and identical across all workers and instances. Set `WHATSAPP_NUMBER=4917642484892` (or the intended international digits-only number). Do not paste secrets into GitHub or this documentation.

See `FINAL_DEPLOYMENT_DIAGNOSTICS.md` for the exact no-reload / CSRF smoke test.
