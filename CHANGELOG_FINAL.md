# Final build change log

- Raised the public case intake limit from 5/hour to a configurable 30/hour default.
- Fixed German WhatsApp international-number normalization for `0049...` and `+49...`; rejects malformed values and the domestic trunk zero after +49.
- Preserved the visitor's chosen language through successful admin login.
- Added localized admin dashboard, case report, receipt, and risk-triage copy for all 11 bundled locales.
- Added accurate all-record dashboard metrics while retaining the latest-250 list view.
- Added CSV spreadsheet-formula neutralization.
- Added a 64 KB request body cap, ProxyFix configuration for one Render proxy hop, and a duplicate-submit UI state.
- Added a compatibility alias for `/private-inbox/logina`; canonical login remains `/private-inbox/login`.
- Added security architecture, threat model, Render Free limitations, deployment instructions, and helper tests.
- Updated Flask to 3.1.3.


## v8 verification fixes

- Fixed startup failure when the admin translation catalog references Portuguese, Turkish, Simplified Chinese, and Japanese before those locales exist in the base catalog. Missing locale dictionaries are now seeded from English before localized labels are applied.
- Added translated admin-shell navigation, login, status, loading, and empty-state labels for those four locales.
- Replaced the admin login page's hard-coded English kicker with a translation key.
- Added the missing required-fields label to the public intake form.
- Normalized Render `postgres://` and `postgresql://` database URLs to the installed `psycopg` 3 SQLAlchemy dialect.
- Corrected local setup instructions: `.env` is not implicitly loaded by `python app.py`; shell environment variables are used instead.
- Hardened CSV formula detection for leading BOM and common invisible whitespace/control characters.


## v9 — UI, accessibility and admin workflow refresh

- Added skip navigation, labelled landmarks, active navigation state, and clear keyboard focus indicators.
- Made the loader progressive-enhancement only so it cannot block no-JavaScript visitors.
- Added 11-locale translated case search, status filters, visible-row counts, empty-filter feedback, triage flags and admin success/error messages for the 250 most recent dashboard rows.
- Added one-click case reference copying with assistive-technology feedback and printable case reports.
- Restored native browser validation, exposed the story counter to assistive technology, and used a native date input.
- Improved contrast for muted placeholders and small interface labels, responsive dashboard controls, and reduced-motion/print behavior.
- Added source-based UI review and regression tests. No new runtime packages were introduced.


## v10 — reliable complete-report WhatsApp hand-off

- Fixed the previous reference-only WhatsApp message: the prefilled draft now includes the saved case reference, all submitted requester and incident fields, the full description, advisory risk indicators, and generated triage report.
- Added a separate explicit consent before sending personal case details to WhatsApp.
- The case is committed to the database before WhatsApp is opened. Database failures roll back, display an error, and never start the WhatsApp hand-off.
- Added a no-store receipt page that automatically redirected to `wa.me` after the case was committed, with a manual fallback button. This automatic behavior was subsequently removed in v11 at the owner’s request.
- Applied `Referrer-Policy: no-referrer` to the case receipt to avoid leaking its page context to WhatsApp; application code does not log the message URL.
- Added a slow-submission status message so users do not see an unexplained endless submit spinner; the button remains disabled while a pending request could still commit.
- Added regression tests for the configured international destination, full message payload, URL encoding, explicit consent and commit-before-handoff ordering.
- Clarified that a normal WhatsApp click-to-chat draft still requires the visitor to press Send; the website cannot observe that final action without an independently configured WhatsApp Business Cloud API/webhook integration.


## v11 — explicit WhatsApp click only

- Removed the JavaScript timer and automatic redirect to WhatsApp.
- The saved-case receipt shows one direct WhatsApp button; the external app/site can open only after the visitor activates it.
- Updated all 11 UI locales to explain that the visitor must click the button and then press Send themselves.
- Added `noopener noreferrer` and `no-referrer` protections to the external hand-off link.
- The case is still committed before the receipt is rendered; no WhatsApp launch is attempted when the number is not configured or valid.


## v12 — one-button create-and-send-to-WhatsApp flow

- Removed the contact-method radio choice, private-inbox alternative, receipt page, and separate WhatsApp hand-off button.
- The contact form now exposes exactly one delivery submit action: **Send to WhatsApp**.
- Every valid submission requires explicit consent for WhatsApp sharing; the database stores `contact_method=whatsapp` for new records.
- The server checks the configured destination, flushes the record, generates the full prefilled report, commits the transaction, and only then issues a 303 redirect to `wa.me`.
- A missing/invalid number or database failure rolls back and prevents external redirect; it does not create a case that cannot be handed off.
- Clarified that the visitor still presses Send inside WhatsApp; a regular click-to-chat URL cannot send automatically or provide delivery confirmation.
- Added translated single-button labels and configuration-error messages for all 11 supported UI locales.
