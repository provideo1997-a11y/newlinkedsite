# Technical review — YAKUZA Private Case Desk

## Delivered in this build
- Flask public website and structured case intake.
- Multilingual public site and intake, including Arabic RTL and Tunisian Arabic.
- Admin dashboard, individual case report, status updates, and protected CSV export.
- Dashboard, case detail, receipt, and risk-triage interface translations for all bundled locales.
- Admin language choice is retained across successful login. Eleven admin locales are initialized safely; four additional admin locales use English fallback on untranslated public-site pages.
- Configurable intake rate limit; default raised from 5/hour to 30/hour.
- CSRF, server-side validation, honeypot, arithmetic challenge, request-size limit, secure cookie options, security headers, and admin session checks.
- WhatsApp number normalization for `0049...`, `+49...`, and digits-only international formats.
- Single-button WhatsApp submission requires explicit consent, commits the full case first, then navigates to a prefilled message with the complete case and generated triage report; the message text is visible in the click-to-chat URL. The visitor must press Send in WhatsApp.
- CSV formula-injection neutralization.
- Accurate dashboard totals beyond the latest 250 displayed records.
- PostgreSQL URL normalization to the installed psycopg 3 driver, and Render deployment configuration.

## Important limitations
- The uploaded project ZIP was inspected and modified. The remote GitHub repository was not changed; authenticated write access was not available in this session.
- No live Render deployment was triggered.
- No production penetration test, independent code audit, or live WhatsApp delivery test was performed.
- Free Render hosting cannot provide permanent uptime or durable case storage. Free Postgres expires after 30 days; local filesystem data is ephemeral. See `RENDER_FREE_LIMITS.md`.
- `memory://` rate limiting is process-local and resets on restart. The public intake endpoint has a configurable 30/hour IP limit, but the app-wide 50/hour default can also apply. This is acceptable for a one-instance demo only.
- Admin MFA, per-action audit logging, email verification, attachment quarantine/scanning, and formal retention automation remain production hardening work.
- The intake path now uses a signed per-form idempotency reference, a unique database constraint, and recovery lookup for concurrent duplicate submissions.

## Test status
Static syntax/structure and ZIP integrity checks should be run before release. A real deployment must also complete the manual end-to-end checklist in `FREE_HOSTING_AND_DOMAIN_GUIDE.md` and `SECURITY_ARCHITECTURE.md`.


## UI/UX and accessibility review (v9)

The v9 interface work is documented in `UI_UX_REVIEW.md`. The existing dark charcoal/lime visual identity and Flask/Jinja plus vanilla JavaScript architecture were retained. The dashboard now supports client-side search and status filtering over the 250 most recent rendered cases, with the existing CSV route retained for full export. Case reports support reference copying and browser printing.

Accessibility work includes skip navigation, semantic main/nav landmarks, current-page nav state, focus-visible rings, localized screen-reader labels, a progressively-enhanced loader, native form validation, and reduced-motion/print rules. These changes were source- and template-tested. They were not certified by an independent WCAG audit or a live assistive-technology test.


## Final submission reliability repair
The intake form has one action only. The browser sends a same-origin JSON request and refuses background redirects; after a successful commit it validates the returned `wa.me` URL and navigates the same tab. The no-JavaScript path receives a normal 303 after commit. PostgreSQL and SQLite waits are bounded; signed idempotency tokens prevent duplicate cases after retries; `/health/db` and support-reference logs help distinguish database failures from browser/platform failures. The visitor still presses Send in WhatsApp. See `FINAL_DEPLOYMENT_DIAGNOSTICS.md` and `BUILD_VERIFICATION.md`.
