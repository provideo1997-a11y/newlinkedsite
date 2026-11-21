# Final deployment diagnostics — secure case submission

## Expected one-button path
1. Visitor completes the form and arithmetic check.
2. Visitor clicks **Send to WhatsApp** once.
3. The browser posts JSON to the same-origin `/contact` endpoint.
4. Flask validates the form, commits the case, then returns a WhatsApp destination.
5. The browser navigates to `https://wa.me/<number>?text=...`; the visitor presses Send inside WhatsApp.

## What the token-renewal defect was
There were two different token error paths. Flask-WTF CSRF failures used `CSRF_TOKEN_REFRESHED`, which the client knew how to process. But an expired/invalid YAKUZA case token was handled inside `/contact` and returned only a message + token fields without a recovery code or refreshed CSRF token. The JavaScript did not apply those fields. That meant the next click reused stale hidden data and could show the same message again.

This repair unifies the two paths. It returns `CASE_TOKEN_REFRESHED`, refreshes the CSRF token, updates the case token and question in the DOM, and focuses the answer field when a genuinely new calculation is required. For a still-authentic token between one and 24 hours old, it re-signs the original challenge and retries the same request automatically.

## Test after deployment
- Use a fresh private/incognito browser tab.
- Open the contact page and complete all required fields, consents and arithmetic check.
- Click **Send to WhatsApp** once.
- Expected: the case is saved, then WhatsApp opens with the full message.
- If a new security check appears, verify the displayed arithmetic question changes and the answer field is focused; solve it and click the same button again.
- Check Render Logs for `intake_committed`, `intake_reused`, or `intake_failure`. These events do not log submitted names, email addresses or incident descriptions.

## Environment invariants
- `SECRET_KEY` must remain stable across deployments and be identical across all running instances. Do not regenerate it during deploys.
- `WHATSAPP_NUMBER` must be digits-only international format (for the configured German number, begin with `49`, not `0049` or `+`).
- `DATABASE_URL` must point to the intended persistent database.
- `/health/db` only confirms database reachability; it does not validate CSRF/session signing.

## If the fresh check keeps reappearing
A repeated new challenge after deployment strongly suggests inconsistent `SECRET_KEY` values between app instances, a secret being changed between GET and POST, or an old deployment/static asset still being served. Confirm all instances use the same exact Render `SECRET_KEY`, check the deployed commit SHA, and hard-refresh/clear the site's cached files once. Do not paste the secret into logs or chat.

## Limits of local verification
Automated tests, helper logic, Python compilation, JavaScript syntax, and template parsing passed here. The real Render browser POST, PostgreSQL commit and WhatsApp launch must still be tested after deployment; this environment cannot access your live Render runtime.
