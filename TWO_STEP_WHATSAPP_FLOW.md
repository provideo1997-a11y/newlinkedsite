# Two-step case and WhatsApp hand-off

1. The visitor fills the normal HTML form and gives the required account-authorization and WhatsApp data-sharing consents.
2. Flask-WTF validates the hidden session CSRF token. The route validates the submitted fields and both consents.
3. The case and advisory triage report are saved and committed to the configured database.
4. Flask returns a 303 redirect to a signed, time-limited `/case/ready/<token>` page. The token contains only the case reference, not personal information.
5. The ready page retrieves the saved case and builds the WhatsApp click-to-chat URL from the saved record. The complete requester details, incident narrative, risk indicators and triage report are prefilled in the message.
6. The WhatsApp link opens in a separate tab/window (or launches the installed WhatsApp app where supported). This keeps the YAKUZA confirmation page available in the original browser tab.
7. The visitor reviews the draft and presses **Send** in WhatsApp. WhatsApp does not permit a website to press Send on the visitor's behalf. After sending, the visitor switches back to the original YAKUZA tab; the saved case confirmation remains available, with a link back to the YAKUZA home page.

## Why this uses a normal form

The intake uses ordinary HTML POST + Post/Redirect/Get. There is no AJAX submission, arithmetic challenge, visible CSRF prompt, or client-side retry loop. The standard hidden Flask-WTF CSRF token, server-side validation, honeypot and rate limiting remain active. If a CSRF token expires, the visitor sees a clear form error and can submit again after the page has refreshed.

## Privacy and reliability

- The hand-off token is signed, expires after 24 hours and contains only the case reference.
- The case is saved before the WhatsApp page is shown. Returning from WhatsApp does not create a duplicate case.
- The WhatsApp draft is generated from the saved database record, not from editable browser fields.
- The WhatsApp provider receives the message only after the visitor reviews and presses Send.
- The confirmation page remains open in the original browser tab while WhatsApp is opened separately.
