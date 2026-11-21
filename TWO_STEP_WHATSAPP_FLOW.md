# Two-step case and WhatsApp hand-off

1. The visitor fills the normal HTML form and gives the required account-authorization and WhatsApp data-sharing consents.
2. Flask-WTF validates the CSRF token; the route validates the signed per-form case reference, field values and consent.
3. The case and advisory report are saved and committed to the configured database.
4. Flask returns a 303 redirect to a signed, time-limited `/case/ready/<token>` page. The token contains only the case reference, not personal information.
5. The ready page retrieves the saved case and builds the complete WhatsApp click-to-chat URL. It displays exactly one WhatsApp action.
6. The visitor clicks the link; WhatsApp opens with the complete case message. The visitor reviews and presses Send inside WhatsApp.

## Why this replaces AJAX

The prior versions used JavaScript `fetch()` plus arithmetic/CSRF retries that could return visitors to a repeated security question. This build removes that visible arithmetic challenge entirely and uses ordinary HTML POST + Post/Redirect/Get. Expired CSRF errors re-render the same form, preserve submitted fields and renew the hidden CSRF token. There is no client-side intake retry loop.

## Privacy and reliability

- The hand-off URL is signed and expires after 24 hours.
- The token carries only the case reference.
- The hand-off page is non-cacheable and sends `Referrer-Policy: no-referrer`.
- Case creation is idempotent by signed per-form case reference. A retry returns the already-saved case.
- WhatsApp does not receive the message until the visitor reviews and presses Send.
