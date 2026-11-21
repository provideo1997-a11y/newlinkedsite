# Final build change log

- Raised the public case intake limit from 5/hour to a configurable 30/hour default.
- Fixed German WhatsApp international-number normalization for `0049...` and `+49...`; rejects malformed values and the domestic trunk zero after +49.
- Reduced WhatsApp URL exposure to the case reference only; no name, email, or incident narrative is placed in the link.
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
