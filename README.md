# YAKUZA — Full Flask Case Intake + WhatsApp + Admin Dashboard

## What this package does
- Public case intake form with validation, CSRF protection, rate limiting and a human check.
- Saves each accepted case to the configured SQL database **before** showing WhatsApp.
- Shows a case reference and a click-to-chat WhatsApp button with a prepared summary.
- Admin dashboard at `/admin/login` to review, filter, update and add internal notes to saved cases.
- Admin case detail includes a WhatsApp contact button when the requester supplied a phone number.
- Public case status lookup at `/status` (can be disabled with `PUBLIC_STATUS_LOOKUP=0`).
- Languages: English, French, Arabic and Tunisian Arabic (`ar-tn`).

## Important: persistent case storage on Render
The included Render web service is configured to read `DATABASE_URL`, but it does not create a database automatically.
For cases to survive web-service restarts/redeploys, set `DATABASE_URL` to a **persistent PostgreSQL database connection string** in the Render web service environment.
Do not use `sqlite:///yakuza.db` for real customer records on Render Free: the web service filesystem is ephemeral and case data can be lost.
A paid/persistent database may incur charges. Check the current Render pricing and database expiry/backup policy before choosing a database plan.
Local SQLite is fine for local testing.

## Deploy to Render
1. Upload this folder to a GitHub repository (keep `.env` and secrets out of Git).
2. In Render, choose **New → Blueprint** and connect the repository, or create a Python Web Service.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn --workers 2 --bind 0.0.0.0:$PORT app:app`
5. Add environment variables:
   - `SECRET_KEY`: a long random secret
   - `ADMIN_USERNAME`: your private dashboard username
   - `ADMIN_PASSWORD`: a long unique password
   - `WHATSAPP_NUMBER`: your WhatsApp Business/support number, digits only, including country code; no `+`, spaces or dashes
   - `DATABASE_URL`: persistent PostgreSQL connection string
   - `COOKIE_SECURE=1` (keep this for HTTPS deployment)
   - `PUBLIC_STATUS_LOOKUP=1`
6. Deploy, then test `/healthz`, `/intake`, and `/admin/login`.
7. Open `/admin/login` and sign in with the credentials you configured.

## WhatsApp behavior
- The website does **not** send WhatsApp messages automatically.
- After a case is saved, the requester can click **Continue on WhatsApp** to open WhatsApp with a prefilled message and case reference.
- Admins can click **Contact requester on WhatsApp** on a case detail page when a phone number was provided.
- WhatsApp must be installed or accessible in the user's browser. The user must press Send inside WhatsApp.
- Configure `WHATSAPP_NUMBER` with your own support number in international digits-only format.

## Local Windows test
```powershell
py -3.13 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m flask --app app run
```
For local HTTP testing, set `COOKIE_SECURE=0`. Use a strong local `SECRET_KEY` and admin password.

## Security and operations
- Do not commit `.env`, database credentials, or production secrets.
- Use HTTPS in production.
- Restrict dashboard access with a strong unique password.
- Back up the database and test restoring backups.
- Do not ask clients to send passwords, recovery codes, identity documents or other unnecessary sensitive material through WhatsApp.
- Automated risk indicators are prompts for human review, not determinations of fraud or wrongdoing.

## Routes
- `/` — home
- `/intake` — submit a case
- `/status` — public status lookup
- `/admin/login` — private dashboard login
- `/admin` — case dashboard
- `/admin/case/<reference>` — case detail and internal notes
- `/healthz` — health check
