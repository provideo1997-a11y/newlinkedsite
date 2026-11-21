# YAKUZA — final submission repair

## Submission / CSRF loop repair
- Removed the explicit browser reload response for AJAX CSRF failures.
- AJAX CSRF failures now return a freshly generated Flask-WTF token, the existing signed case token when valid, and a retryability flag.
- Client refreshes hidden tokens and retries once without reloading the page.
- If the signed case token itself has expired, the client updates the arithmetic challenge and asks the visitor to solve it again using the same single submit button.
- Removed all `window.location.reload()` calls from the intake interaction.
- Added a cache-busting query parameter to the main JavaScript asset so browsers fetch the updated submit handler.
- Set the form action explicitly to the canonical `/contact` endpoint.
- Language query cleanup now redirects GET requests only, never POST submissions.

## Existing one-button behavior retained
- One public submit button: **Send to WhatsApp**.
- Case is validated and committed before WhatsApp hand-off.
- Full case report is prefilled in the WhatsApp chat.
- Duplicate-safe signed case references remain in place.
- WhatsApp still requires the visitor to press Send in the app.
