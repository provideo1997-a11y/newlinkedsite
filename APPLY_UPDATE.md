# Apply YAKUZA v12 — single-button WhatsApp intake

1. Back up your existing GitHub repository and the production database before replacing files.
2. Extract the complete ZIP. Its files are at the archive root; do not copy an extra enclosing folder.
3. Replace the old project source files with all archive contents. Preserve `.git/`, `.env`, database files, `instance/`, customer uploads, and backups. Never commit live secrets or customer records.
4. In Render → Web Service → Environment, set `WHATSAPP_NUMBER` to the destination in international digits only. Example: `4917642484892` (no `+`, spaces, `00`, or domestic trunk zero). Keep all existing admin/database/secret settings.
5. Commit and push to the branch connected to your existing Render service. Do not force-push.
6. After deployment, use a controlled dummy case to test the complete flow.

## Exact one-action behavior

- The contact form has one submit button: **Send to WhatsApp**. There is no delivery-method choice, receipt page, second WhatsApp button, or alternate path.
- The server requires explicit consent to include the submitted personal details in WhatsApp.
- The server validates the configured WhatsApp destination, flushes the new case, builds the full message, and commits the case. Only after a successful commit does it issue a `303` redirect to `https://wa.me/` with the full message prefilled.
- If the WhatsApp number is missing/invalid or the database save fails, the transaction is rolled back and no WhatsApp redirect occurs.
- WhatsApp still requires the visitor to review the draft and press **Send**. An ordinary `wa.me` link cannot press Send or report delivery back to the website.

## Render commands

- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Root Directory: blank when `app.py` is in repository root.
- Health Check: `/health`

Do not overwrite `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DATABASE_URL`, `COOKIE_SECURE`, `ADMIN_URL_PREFIX`, or rate-limit settings unless you intentionally need to rotate/configure them. Keep the real WhatsApp number in Render Environment only; do not hardcode it in Git.

## Deployment checks

1. Open `/contact` and confirm only one primary form submit button is shown.
2. Confirm the WhatsApp-sharing consent and account-authorization checkboxes are required.
3. Submit one dummy case; confirm the browser goes directly to the correct WhatsApp chat with the full prefilled case summary.
4. Confirm the case is visible in the protected admin dashboard even before pressing Send in WhatsApp.
5. Press Send in WhatsApp and confirm receipt on the destination account.
6. Test a missing/invalid destination in a staging environment; the app should show a configuration error and create no case.

A live Render deployment, production database transaction, and device-level WhatsApp send are not verified by this source package.
