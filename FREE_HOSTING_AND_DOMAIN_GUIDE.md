# Free hosting and domain proposal for YAKUZA

## Short answer

There is no responsible way to promise **free lifetime hosting or a free lifetime domain**. Providers can change free plans, suspend inactive or over-quota services, or discontinue a subdomain. A free provider subdomain is the realistic no-cost option; a custom `.com`/`.net` domain normally has a registration and renewal fee.

## Recommended no-cost launch: Render + its free subdomain

This project is a Flask application with server-side forms and a private administrator inbox, so it needs a Python web-service host. Render supports Python web services and assigns an `onrender.com` address. The included `render.yaml` is configured for this deployment.

1. Create a GitHub account and a **private** repository.
2. Extract the ZIP and upload the contents of the `yakuza_enterprise` folder to the repository root.
3. Create a free account at https://render.com/ and choose **New → Blueprint** (or **New → Web Service**).
4. Connect the repository containing `render.yaml`.
5. Supply `ADMIN_USERNAME` and `ADMIN_PASSWORD` when prompted. Use a unique password of at least 14 characters.
6. Confirm the service uses the Free plan and deploy.
7. Render will assign an address similar to `https://yakuza-digital-agency.onrender.com`. The exact name depends on availability and may need to be adjusted in the dashboard.
8. Test `/`, `/contact`, `/health`, and `/private-inbox/login`. Submit a dummy inquiry and confirm it appears only after admin login.

The Blueprint configures the WhatsApp destination as `4917642484892` (+49 176 42484892). If the number changes, update `WHATSAPP_NUMBER` in Render's Environment settings and redeploy.

## Free-tier limitations you must understand

- Render Free web services spin down after 15 minutes without inbound traffic and can take around a minute to wake up.
- Free web services have an ephemeral filesystem. Local SQLite records can be lost on spin-down, restart, or redeploy.
- Render's Free Postgres currently expires after 30 days and has no backups. Do not use it as permanent client-message storage.
- Free plan limits, quotas, and availability can change. This is a free launch option, **not a lifetime service-level guarantee**.
- Use a durable database with backups and suitable paid hosting before handling real customer cases.

## Why not GitHub Pages?

GitHub Pages is excellent for static HTML/CSS/JavaScript websites, but it does not run this project's Flask/Python backend, private inbox, authentication, or database. Moving to GitHub Pages would require rebuilding the app as a static frontend and moving its backend elsewhere.

## Other option: PythonAnywhere

PythonAnywhere has a limited free Beginner account, but its current published limits include a single web app with a one-month expiry, 100 CPU seconds, and 512 MiB storage. It is not a stronger lifetime guarantee. Check the provider's current terms before choosing it.

## Practical proposal

Start with Render's free `onrender.com` subdomain to publish a preview without buying a domain. Keep the GitHub repository private, use strong admin credentials, and do not store real client records until persistent database storage, backups, and retention rules are configured. When the agency is ready for dependable business use, budget for a registered domain and reliable hosting rather than relying on a free tier indefinitely.
