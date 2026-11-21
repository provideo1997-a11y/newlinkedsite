# Final change log — WhatsApp case submission recovery

## Confirmed defect fixed
The route's own expired/invalid case-token handler returned replacement case token data but did not follow the response contract expected by the browser. The browser therefore failed to update the hidden case token / visible check and the same stale submission repeated.

## Changes
- Added `CASE_TOKEN_REFRESHED` JSON response contract with refreshed CSRF + case token and arithmetic question.
- Client now handles both `CSRF_TOKEN_REFRESHED` and `CASE_TOKEN_REFRESHED`, updates form values, clears/focuses a replacement challenge, and never forces a reload.
- Added a 24-hour renewal grace for authentic one-hour tokens; a refreshed token retains the original case reference and arithmetic challenge.
- Bad signatures / old signing secrets / tokens outside the grace period receive a genuinely new challenge and reference, correctly exposed in the form.
- Bumped the JavaScript cache key.
- Added regression tests for route-level JSON contract, in-place DOM update, authentic expired-token renewal, and old-secret recovery.
