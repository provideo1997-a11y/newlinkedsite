# YAKUZA — UI/UX Review and v9 Upgrade

## Scope and evidence

This review is based on the actual v8 source included in the working package: the shared Jinja shell, public landing and intake templates, admin dashboard, case report, CSS, and vanilla JavaScript. The request history also reports that the admin needed usable translations and that the loading animation should be improved.

No product analytics, error-rate dashboard, user interview notes, session recordings, accessibility audit, or performance trace was supplied. Accordingly, the findings below are source-level observations, not claims about measured user behavior or Core Web Vitals.

## Current UI assessment

### Usability

- The existing visual language is distinctive: charcoal surfaces, lime accent, geometric art, strong headlines, and a consistent header/footer.
- The intake form is structured into identity, incident and follow-up sections. It collects useful case context but is long and dense; mobile layout stacks fields into one column.
- The admin dashboard had useful aggregate cards and a case table, but no quick search or status filter. An operator had to rely on browser find or export for triage.
- Case detail already displayed requester information, evidence link, advisory indicators, narrative and status controls, but did not provide a quick way to copy the case reference or print a clean report.
- The table is intentionally wider than a phone viewport and scrolls horizontally. This is workable, but users need a keyboard-accessible scroll container and a clear explanation of which records are currently loaded.

### Accessibility

- The shared shell already set the document language and text direction and used semantic header, nav, main and footer elements. It lacked a skip link and the main landmark did not have a stable focus target.
- Keyboard focus styling was inconsistent because several controls removed their outline without a reliable replacement.
- The page loader was present in the markup as a visible fixed overlay. If JavaScript failed or was disabled, the overlay could remain above the site.
- The case form used `novalidate`, disabling native browser validation even though controls declared required/minimum/maximum constraints.
- Some subdued microcopy and form placeholders were low contrast against their dark surfaces (for example, the placeholder token was below 4.5:1 against its field surface).
- The design already had a reduced-motion media rule, but the loader and newly added interaction states needed a consistent policy.

### Aesthetic and responsive behavior

- The dark/lime identity is cohesive and appropriate to a digital-risk intake product. The main risk is overuse of tiny monospaced labels and atmospheric detail in operational views.
- The landing page is intentionally cinematic. The admin area benefits more from hierarchy, scannability, strong labels and clear actions than from extra animation.
- Mobile breakpoints already stacked the primary navigation and dashboard metrics. The wide data table still needs horizontal scrolling, so the table region is now focusable and labelled.

## Changes shipped in v9

1. **Dashboard filters:** Search the visible case rows by reference, name, email, category, platform or other row text, and filter by New / Reviewing / Closed. The visible count updates immediately and a no-match row appears when needed. This is client-side filtering over the 250 most recent cases the server currently loads; it does not claim to search the entire database. CSV export remains the full export route.
2. **Case report actions:** Copy the case reference with success/failure feedback for assistive technology and print a simplified report using browser print support.
3. **Accessible navigation:** Added a localized skip link, a named navigation landmark, `aria-controls` on the mobile menu, active-page state, and a consistent visible keyboard focus ring.
4. **Progressive loader:** The overlay is hidden by default and shown only after JavaScript marks the page as enhanced. Without JavaScript the website remains usable. The loader reports its progress state and closes on page load or a bounded timeout.
5. **Intake validation:** Restored native browser validation, used a native date input, and associated the character counter with the report textarea.
6. **Readability:** Increased contrast for muted placeholders and small interface labels, improved filter spacing on small screens, and added consistent reduced-motion and print rules.
7. **Localization:** New navigation/accessibility labels, dashboard controls, counts, report actions, status-update feedback, login errors, submit-progress announcements and triage-flag labels are included in all 11 bundled admin locales: English, French, Arabic, Tunisian Arabic, Spanish, German, Italian, Portuguese, Turkish, Simplified Chinese and Japanese.

## Compatibility and performance

- No new runtime dependencies, frontend framework, CDN, web font, tracking script or external API is introduced.
- The dashboard filter is O(n) over at most 250 DOM rows per input event, small enough for the current server-side limit. It uses native input/select controls and no third-party table widget.
- Copy uses the browser Clipboard API on secure contexts and a local selection fallback otherwise. No case data is sent to a third party.
- Print uses `window.print()` and CSS; no PDF-generation service is involved.
- The loader does not add a render-blocking external request and cannot obstruct the no-JavaScript path.

## Recommended roadmap (not represented as implemented)

| Priority | Proposal | Why it matters | Existing-stack fit / trade-off |
|---|---|---|---|
| P1 | Server-side search, date range and pagination | Finds old cases beyond the recent 250 | Flask + SQLAlchemy filters and indexed columns; adds query/index and pagination testing. |
| P1 | Case activity timeline with actor and timestamp | Makes status changes and hand-offs accountable | Add an append-only SQLAlchemy event model; more writes and schema migration, but stronger auditability. |
| P1 | Operator assignment and role-based access | Reduces shared-admin-account risk | Add admin roles and per-route authorization; requires careful migration and an authorization matrix. |
| P2 | Saved dashboard views and keyboard shortcuts | Speeds up repetitive triage | Small vanilla-JS enhancement; avoid localStorage for sensitive search strings. |
| P2 | Evidence attachment flow with strict allowlist, size limits, malware scanning and private object storage | Avoids reliance on public links | Requires a private storage provider and scanning pipeline; not suitable for a simple free-only deployment. |
| P2 | Accessibility regression suite (axe-core in CI plus manual keyboard/screen-reader checks) | Prevents regressions across 11 locales and RTL | Add development-only tooling and CI runtime; does not replace human testing. |
| P3 | Read-only PWA shell for operator convenience | Faster repeat visits and clearer offline state | Cache only static shell assets; never cache private case data or authenticated HTML. |

## Validation boundary

The v9 source is checked with Python compilation, JavaScript syntax validation, pytest, Jinja syntax parsing and representative Jinja rendering, and YAML parsing. The build environment did not have Flask dependencies installed and could not reach the package index; therefore full Flask startup, live database integration, production browser testing, assistive-technology certification, Render deployment, and WhatsApp delivery were not verified in this environment.


## Final case-intake interaction — two-page Post/Redirect/Get
The public intake is now deliberately split into two simple pages. Page 1 uses a normal HTML POST with native browser validation, Flask-WTF CSRF protection, a honeypot and server-side rate limiting; the recurring arithmetic challenge has been removed. A successful request saves the case and triage report, then returns a 303 redirect to a signed case-ready page. Page 2 displays the case reference and a concise summary, plus exactly one **Send to WhatsApp** link. Clicking the link opens the prepared full message; the visitor reviews and presses Send in WhatsApp.

The intake JavaScript no longer intercepts submission, starts a fetch request, retries CSRF tokens, or navigates after parsing JSON. If CSRF expires, the server re-renders the same form with entries preserved and a refreshed CSRF token. No visible arithmetic challenge or client-side retry state remains. The WhatsApp page token contains only the case reference, expires after 24 hours, and the page is non-cacheable with no-referrer policy.
