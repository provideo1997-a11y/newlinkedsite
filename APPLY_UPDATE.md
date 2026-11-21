# Apply the YAKUZA final reliability repair

This archive contains the complete application at its repository root.

## Before replacing files

1. Back up the entire GitHub repository and export the current production database.
2. Extract this ZIP to a clean temporary folder.
3. Open your existing repository working folder.
4. Replace the old project source and documentation with every file from this archive.
5. Preserve `.git/`, the local `.env`, any private uploads, database files, `instance/`, and backups. Never overwrite or commit production secrets/data.
6. Check `git status` and review the full staged diff before committing.

## Render environment

Keep the existing stable `SECRET_KEY`, admin credentials, database URL, cookie setting and admin path. Confirm these values are present:

```env
COOKIE_SECURE=1
ADMIN_URL_PREFIX=/private-inbox
WHATSAPP_NUMBER=YOUR_DIGITS_ONLY_INTERNATIONAL_NUMBER
INTAKE_RATE_LIMIT=30 per hour
RATELIMIT_STORAGE_URI=memory://
```

Keep the WhatsApp number you already configured in Render Environment; it is not embedded in source. Use the international country code followed by the subscriber number, digits only. Do not put `+`, `00`, spaces or the domestic trunk prefix after the country code.

`DATABASE_URL` must point to an active PostgreSQL database. An expired or unreachable database cannot save new cases. The local SQLite fallback is for development only and is not durable on Render Free.

## Render service settings

- Root Directory: blank (when `app.py` is in repository root)
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Health Check Path: `/health`

Do not change the deployed service's start command or delete the database. Push to the branch configured for automatic deployment; do not force-push.

## Verify after deployment

1. Open `/health`. It should return `{"status":"ok","service":"yakuza"}`.
2. Open `/health/db`. It should return HTTP 200 and `database: reachable`. A 503 means the database path must be fixed before intake can work.
3. Open `/contact`; complete a controlled dummy report and required consent fields.
4. Click the only button, **Send to WhatsApp**. The case must commit first, then the same browser tab must open the configured WhatsApp draft with the full details.
5. Confirm the saved case appears in the protected admin dashboard even before the visitor presses Send in WhatsApp.
6. Press Send in WhatsApp and confirm the message reaches the configured account.

## If submission still fails

The page will show a support reference. In Render Logs search for `intake_failure` and the reference. Read the `stage` and `error_type` fields. No case contents or credentials are written to the log. If there is no matching line, check Render deploy/service logs and confirm this commit is deployed.

The browser allows 120 seconds for a request and uses a signed per-form case reference so retrying after a lost response will not create a duplicate. Startup ensures a unique case-reference index exists even on upgraded databases. If the existing database already has duplicate non-null references, startup stops and logs a migration error instead of weakening idempotency. PostgreSQL connection/pool/lock/statement waits and SQLite lock waits are bounded.

## WhatsApp limitation

A `wa.me` link opens WhatsApp with prefilled message text. It cannot automatically press Send from the visitor's account and cannot notify the website that the visitor sent it. The visitor must press Send inside WhatsApp. The case is saved before the hand-off.
