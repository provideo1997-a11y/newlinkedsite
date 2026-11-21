# Final deployment diagnostics

The intake path uses ordinary browser form submission and Post/Redirect/Get. There is no AJAX handler, visible arithmetic challenge or background WhatsApp redirect.

## Expected route sequence

1. `GET /contact` returns a form containing a Flask-WTF CSRF token and a signed per-form idempotency reference.
2. The visitor completes the fields, checks account authorization and WhatsApp data-sharing consent, then clicks **Create secure case**.
3. `POST /contact` validates CSRF, WTForms fields, the signed per-form reference, honeypot, consent and the configured WhatsApp destination.
4. The server saves the case and triage report in the database, commits, then returns `303 Location: /case/ready/<signed-token>`.
5. The case-ready page validates the 24-hour signed token, fetches the saved case and displays exactly one **Send to WhatsApp** link.
6. Clicking that link opens `https://wa.me/<number>?text=<complete-report>`. The visitor reviews the message and presses Send inside WhatsApp.

## If the form shows an error

- Ordinary field-validation errors re-render the form and retain the submitted values. Blank optional phone, incident-date, account-handle and evidence fields are normalized to empty strings before database insertion, avoiding `None.strip()` crashes.
- CSRF expiry re-renders the form, preserves the submitted values and supplies a fresh hidden CSRF token. The signed per-form case reference is reused when authentic, so retrying after a lost response cannot create a duplicate case.
- The arithmetic challenge was removed to eliminate the repeated visible test that previously blocked submissions. Anti-abuse controls are the CSRF token, signed form reference, hidden honeypot, request-size limit and server-side rate limiting.
- Database or WhatsApp configuration failures are shown on the form with a support reference; the case is not intentionally redirected to WhatsApp unless it has been saved.
- If the case committed but the redirect response was lost, re-submitting the same signed per-form reference reuses the existing record and returns the visitor to the case-ready page.

## Deployment notes

Keep `SECRET_KEY` stable across deploys and all workers. Keep `DATABASE_URL` pointing at the persistent database and `WHATSAPP_NUMBER` in international digits-only format. Check Render Logs for `intake_failure` entries; logs include a support reference, processing stage and exception type, not the visitor's personal content.
