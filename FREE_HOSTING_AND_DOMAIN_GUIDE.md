# Render setup guide

The app can be tested on Render Free, but Render Free is not permanent production hosting for private case data. Read `RENDER_FREE_LIMITS.md` before launch.

## Create/update the Web Service
1. Push the contents of `yakuza_enterprise/` to the root of your GitHub repository (so `app.py`, `requirements.txt`, and `render.yaml` are at repository root).
2. Render Dashboard → New → Blueprint if you want to use `render.yaml`, or open the existing Web Service and configure it manually.
3. Select the GitHub repository and production branch.
4. Root Directory: blank.
5. Build: `pip install -r requirements.txt`
6. Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
7. Health check: `/health`
8. Plan: Free for a demo only.
9. Add the environment variables below and deploy.

## Environment variables
| Key | Value |
|---|---|
| `SECRET_KEY` | Generate a strong random value; never reuse a leaked key |
| `ADMIN_USERNAME` | Your chosen admin login |
| `ADMIN_PASSWORD` | Unique password, 16+ characters |
| `COOKIE_SECURE` | `1` |
| `ADMIN_URL_PREFIX` | `/private-inbox` |
| `WHATSAPP_NUMBER` | `0049...` or `+49...`, international format; omit the national leading zero after country code |
| `INTAKE_RATE_LIMIT` | `30 per hour` |
| `RATELIMIT_STORAGE_URI` | `memory://` for single-instance demo only |
| `DATABASE_URL` | PostgreSQL Internal Database URL; required before real case data |

Never paste secrets into GitHub, chat, screenshots, source files, or README.

## Fixing the WhatsApp number
For a German number:
- If the number is written as `0049 17...`, the app removes `00` and separators.
- If written as `+49 17...`, the app removes `+` and separators.
- The final `wa.me` URL uses digits only, e.g. `4917...`.
- Do not include Germany's domestic trunk `0` after `49`.
- Confirm the WhatsApp account is registered and can receive messages.

## Verify after deployment
1. Open `/health` and confirm JSON status `ok`.
2. Open the homepage and switch every language.
3. Submit a clearly fake test case, then confirm the generated reference.
4. Log in at `/private-inbox/login`.
5. Confirm the record appears in the dashboard and the detail page.
6. Change status and confirm it persists after refresh.
7. Export CSV and inspect values.
8. Test WhatsApp hand-off with a test number. Confirm the case is already present in the dashboard before the redirect.
9. Delete the dummy case manually only after testing (the current UI has no delete action; use the database admin/SQL workflow carefully).

## Existing service update
Do not create a second service if you want to keep `newlinkedsite.onrender.com`. Update the existing GitHub repository files, commit, then let the linked Render service deploy. Confirm the service is linked to the intended repository and branch first.
