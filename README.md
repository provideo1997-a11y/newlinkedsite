# YAKUZA — Private Case Desk

Flask case-intake and review portal.

## Deploy
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`
- Set `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` (14+ characters), `ADMIN_URL_PREFIX=/private-inbox`, `COOKIE_SECURE=1`, and `WHATSAPP_NUMBER` in Render.
- Optional production database: `DATABASE_URL` (managed PostgreSQL).

## Intake
Visitors create a case reference, choose one of eight service categories, complete a human check, and select private review or WhatsApp. Automated risk flags are advisory only.

## Languages
English, French, Arabic and Tunisian Arabic have dedicated intake translations. Other existing site languages use English fallback for newly added intake copy.

Never request passwords, one-time codes, recovery keys or payment credentials. See `TECHNICAL_REVIEW.md` for implementation notes.
