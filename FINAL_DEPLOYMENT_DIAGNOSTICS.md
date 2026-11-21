# Final deployment diagnostics

## Why a submission could reload the contact page
The previous client explicitly called `window.location.reload()` when Flask-WTF rejected a CSRF token. This hid the actual CSRF problem behind a page refresh. A stale browser-cached JavaScript file could keep doing the same after a code deployment.

## What this repair changes
1. The AJAX CSRF handler generates a fresh CSRF token and returns it as JSON.
2. When the signed per-form case token is still valid, the browser updates its hidden CSRF field and retries the same submission exactly once.
3. If the per-form token expired too, the server supplies a new case token and arithmetic challenge; the user solves the challenge and uses the same sole button again.
4. The intake JavaScript no longer reloads the current page automatically.
5. The asset URL has a new version query key, forcing browsers to fetch the repaired JavaScript.
6. The form targets the canonical contact endpoint; language query cleanup only redirects GET requests.

## After deployment
1. Open the public contact form in a private/incognito window.
2. Confirm browser DevTools → Network loads `static/js/app.js?v=csrf-refresh-20261121` with HTTP 200.
3. Submit a dummy case once.
4. The POST `/contact` should respond with JSON `ok: true`; the browser should then navigate to `https://wa.me/<digits>?text=...`.
5. If a CSRF response occurs, it should be JSON `code: CSRF_TOKEN_REFRESHED`, followed by one automatic retry; it must not reload the page.
6. In Render Logs, search for `intake_failure` and inspect only the `stage`, `error_type`, and support reference. Do not publish the full WhatsApp URL or case details.

## Environment invariants
- `SECRET_KEY` must be a stable, long random value and must be identical across all running workers/instances. Do not rotate it during a visitor's active form session.
- Keep `WHATSAPP_NUMBER` as an international digits-only or normalizable number (for example `4917642484892`).
- Keep HTTPS and `COOKIE_SECURE=1` on Render.
- The configured database must pass `/health/db` before accepting real cases.
