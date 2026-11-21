# Apply YAKUZA v11 — WhatsApp button-only hand-off

1. Back up the current repository and database.
2. Extract the complete ZIP into a temporary folder.
3. Replace the application source in the existing repository with the archive contents. Keep `.git/`, the live `.env`, `instance/`, uploaded/private evidence, and database backups.
4. Do not commit real secrets or local database files.
5. Keep Render's `WHATSAPP_NUMBER` environment variable set to your destination in international digits-only format. Example shape: `49...`; do not add `+`, spaces, or `00`.
6. Commit and push the existing deployment branch. Render should redeploy the connected service.
7. Submit a controlled dummy case, confirm the receipt and database record, then click the WhatsApp button. Verify that the correct chat opens with the complete prefilled message. Review it and press Send manually.

## Exact hand-off behavior

- The visitor selects WhatsApp and separately consents to share the submitted information.
- The server validates and commits the case first.
- The receipt page then shows a single WhatsApp button. The page does not auto-open WhatsApp, use a timer, or redirect on load.
- Only clicking the button navigates to the WhatsApp click-to-chat URL with the message prefilled.
- The visitor remains the sender and must press Send in WhatsApp. A website cannot detect or force that final action using an ordinary `wa.me` link.

## Render settings

- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Keep `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `COOKIE_SECURE=1`, `ADMIN_URL_PREFIX=/private-inbox`, `DATABASE_URL`, and rate-limit variables configured as before.
- `WHATSAPP_NUMBER` must be entered under Render → Web Service → Environment. Do not place the production number or credentials in committed source files.

## Deployment verification not performed here

The source archive is statically and unit tested. A real Render deployment, production PostgreSQL transaction, device-level WhatsApp app launch, and actual message delivery must still be tested in your deployment environment.
