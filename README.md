# YAKUZA Digital Recovery Agency — Enterprise Cyber Edition (Final v6)

A server-rendered Flask website with a premium cyber interface, cinematic loading intro, custom-generated artwork, responsive layouts, 10 interface languages, Arabic RTL, secure inquiry workflow, and a password-protected team dashboard.

## Final v6 configuration

- WhatsApp contact destination is preconfigured as **+49 176 42484892** (international digits-only value: `4917642484892`).
- Render Blueprint and `.env.example` include the WhatsApp destination so the WhatsApp contact choice works after deployment.
- Review the number carefully before publishing; it will be visible to visitors indirectly through the WhatsApp contact action.

## What is upgraded in v5

- Larger, more readable typography and improved spacing on desktop and mobile.
- Responsive desktop/tablet/mobile navigation, touch-friendly form controls, and mobile-first layouts.
- Cinematic loading intro with animated progress, orbital rings, and reduced-motion support.
- New optimized WebP artwork: shield/globe hero scene and global network scene.
- Animated hero art, orbital radar, scroll reveals, pointer lighting, and reading-progress line.
- 10 languages: English, Arabic, French, Spanish, German, Italian, Portuguese, Turkish, Simplified Chinese, and Japanese. Arabic uses RTL layout.
- Flask server-rendered pages: home, capabilities, about, contact, privacy, and team portal.
- Inquiry workflow with server-side validation, CSRF protection, honeypot, and rate limiting.
- Admin login with hashed passwords, case status updates, and protected CSV export.
- SQLite for local development; PostgreSQL supported through `DATABASE_URL`.
- Security headers, secure-cookie option, health endpoint, and Render deployment blueprint.

## Local setup (Windows 10/11)

1. Install Python 3.12.
2. Extract the ZIP and open PowerShell inside the `yakuza_enterprise` folder.
3. Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Configure local secrets for this terminal session:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_USERNAME = "owner"
$env:ADMIN_PASSWORD = "choose-a-unique-password-at-least-14-characters"
$env:COOKIE_SECURE = "0"
```

5. Start the site:

```powershell
python app.py
```

6. Open `http://127.0.0.1:5000`.
7. Team login: `http://127.0.0.1:5000/team/login`.

The first startup creates the admin account only if both `ADMIN_USERNAME` and an `ADMIN_PASSWORD` of at least 14 characters are supplied. The account is not overwritten on later restarts. If credentials need rotating after creation, use a planned database/admin migration rather than assuming that changing environment variables will reset the existing password.

## Free public deployment (Render)

Render currently offers free web services with an `onrender.com` subdomain. It also supports custom domains, but a custom domain name normally needs to be registered separately. A free Render service is suitable for a demo or preview, not for a business handling real customer case data.

1. Create a GitHub account and a **private** repository.
2. Extract this ZIP. Upload the contents of the `yakuza_enterprise` folder to the repository root (do not upload the ZIP as a single file).
3. Sign in to Render and choose **New → Web Service**.
4. Connect the GitHub repository.
5. Set:
   - Runtime: `Python 3`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
   - Instance plan: `Free`
   - Health check path: `/health`
6. Add environment variables in Render:
   - `SECRET_KEY`: a long random secret; never publish it.
   - `ADMIN_USERNAME`: your private admin username.
   - `ADMIN_PASSWORD`: a unique password of at least 14 characters.
   - `COOKIE_SECURE`: `1`
   - `WHATSAPP_NUMBER`: preconfigured as `4917642484892` (+49 176 42484892); change it in Render Environment if needed
   - `DATABASE_URL`: leave unset only for a disposable demo; set it to a durable PostgreSQL connection URL before accepting real inquiries.
7. Click **Create Web Service** and wait for the build/deploy to finish. Render assigns the actual free address, such as `https://your-service-name.onrender.com`.

You can alternatively use the included `render.yaml` Blueprint and supply the admin secrets when prompted.

## Important free-hosting limits and client-data warning

Render's free web service spins down after 15 minutes without inbound traffic and can take about a minute to wake up. Its filesystem is ephemeral: SQLite records stored on the service can disappear after restart, redeploy, or spin-down. Render's free Postgres database currently expires 30 days after creation and has no backups. Do not use the free Render service with local SQLite or an expiring free database for actual client case records.

Before accepting real customer information, connect a durable PostgreSQL database, configure encrypted backups and test restores, use a persistent rate-limit store if scaling beyond one worker, add monitoring/alerting, define retention/deletion policies, review the privacy notice for your jurisdiction, and use a suitable paid hosting plan. The app does not include file uploads or payment processing.

## Functional routes

- `/` — Home
- `/services` — Capabilities
- `/about` — About
- `/contact` — Secure inquiry form with support-inbox or WhatsApp contact choice
- `/privacy` — Privacy information
- `/team/login` — Team sign-in
- `/team` — Protected inquiry dashboard
- `/team/export.csv` — Protected CSV export
- `/health` — Health check

## Security and acceptable use

YAKUZA is an independent consultancy. Recovery assistance is limited to accounts owned by the requester or covered by clear authorization, using official platform recovery processes. The site must not be used to bypass platform security, impersonate account owners, or obtain unauthorized access. It never asks customers to submit passwords, one-time codes, recovery keys, session cookies, payment card data, or remote-access credentials. Account recovery cannot be guaranteed.

## Project structure

```text
yakuza_enterprise/
├── app.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── render.yaml
├── .env.example
├── README.md
├── templates/
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── img/
│       ├── mark.svg
│       ├── yakuza-shield.webp
│       └── yakuza-network.webp
└── instance/  # local SQLite database generated at runtime; not shipped
```


## Private message inbox (v4 security update)

Public visitors can submit the contact form, but submitted messages are **not displayed on public pages**. They are stored in the application database and can only be viewed after signing in to the private team inbox. The public footer no longer links to the sign-in page.

- Sign-in URL: `/private-inbox/login`
- Private inbox: `/private-inbox`
- Message export: `/private-inbox/export.csv` (authenticated session required)
- Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in your hosting environment. Use a unique password of at least 14 characters.
- Optional: set `ADMIN_URL_PREFIX` to a different private path, e.g. `/team-vault-<random-suffix>`. It must begin with `/`. Changing the path is an additional layer of obscurity, **not a replacement for authentication**.
- Private pages and exports send `no-store` and `noindex` headers. Admin sessions expire after 30 minutes of inactivity.
- All case updates, CSV exports, and logout actions require an authenticated session; forms use CSRF protection.

### Production privacy checklist

1. Deploy behind HTTPS and keep `COOKIE_SECURE=1`.
2. Use a managed, durable PostgreSQL database and configure `DATABASE_URL`; do not rely on an ephemeral free-host filesystem for customer records.
3. Use a long random `SECRET_KEY`, a unique admin username, and a strong password. Never commit `.env` or credentials to GitHub.
4. Restrict access to the hosting provider and database; enable database backups and retention controls.
5. Collect only information needed to respond. Never ask visitors to submit passwords, one-time codes, recovery keys, or payment data.
6. Test the private inbox with a dummy inquiry before accepting real customer data.


## Contact routing: private support inbox or WhatsApp

The contact form now lets visitors choose one of two routes after entering their details:

1. **Contact support** — validates the form and stores the inquiry in the password-protected private inbox.
2. **Continue on WhatsApp** — validates the same fields, then opens the official `wa.me` chat with a pre-filled message containing the visitor's name, email, selected platform, topic, optional phone number, and issue description. The visitor reviews the draft and presses Send in WhatsApp. This route does **not** save the message in the YAKUZA database.

Configure `WHATSAPP_NUMBER` in Render → Environment using the full international number as digits only (country code + number; no plus sign, spaces, or punctuation). The current configured destination is `4917642484892` (+49 176 42484892). This is an intentional public contact destination supplied by the site owner. If the variable is empty, the WhatsApp option displays a configuration warning and the visitor can still use Contact support.

WhatsApp is an external service. Its own account, device, privacy, and availability requirements apply. The site cannot guarantee delivery or read receipts.
