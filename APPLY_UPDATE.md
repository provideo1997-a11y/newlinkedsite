# Apply this update to the existing GitHub repository

This release is packaged with `app.py`, `requirements.txt`, `render.yaml`, templates, static assets, tests, and documentation at the archive root. Extract the archive into the root of the existing `newlinkedsite` repository, replacing only the matching project files. Do not upload `.env`, `instance/`, database files, backups, screenshots containing credentials, or any other private data.

Before replacing files, use GitHub's commit history or a local clone to preserve any changes made after the uploaded source archive. This release is based on the uploaded YAKUZA project, not a live read of the remote repository.

## Commit from a local clone

On macOS/Linux or Git Bash, run `./COMMIT_UPDATE.sh`. On Windows PowerShell, run `./COMMIT_UPDATE.ps1`. Each script stages only the files belonging to this project, checks the staged diff, creates a commit, and attempts to push the current branch to `origin`. Review the staged file list before running it.

If `git status` shows unrelated local work, stage only the files from this release instead of using `git add .`. Do not force-push.

## Existing Render service

Keep the currently linked Render service and its deployment branch. Push the commit to that branch, then allow the existing service to deploy. Do not create a second service from `render.yaml`. Preserve the existing `DATABASE_URL` and confirm it points to the intended database before deploying. Preserve existing admin bootstrap variables where they are in use; they are only needed for initial provisioning or a deliberate password reset. The app now uses the installed psycopg 3 driver for PostgreSQL URLs.

## Required checks after deployment

1. `/health` returns `200` and `{"status":"ok","service":"yakuza"}`.
2. The public form opens in all available locales.
3. The admin login, dashboard, case report, status update and CSV export work.
4. The admin language selection remains selected after login.
5. A test number entered in `WHATSAPP_NUMBER` produces a valid `wa.me` link.
6. Confirm the test case is present in the intended persistent database before accepting real submissions.

This repository update does not migrate or delete existing database records. The application performs the existing additive schema migration at startup; take a database backup before deployment when real records are present.
