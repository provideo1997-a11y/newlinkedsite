# Final change log

- Replaced the brittle one-page AJAX/security-question workflow with a two-page server-rendered flow: create case, save and commit, then open the saved-case page.
- Removed the repeated arithmetic challenge and all stale labels for the retired one-page contact-choice UI. CSRF protection remains enabled.
- CSRF failures re-render the form with entries preserved and a renewed hidden token; there is no user-visible math question to repeat.
- Fixed blank optional fields so an omitted phone, incident date, account handle or evidence URL cannot raise an AttributeError during case creation.
- Case creation is idempotent by a signed per-form case reference and a database uniqueness constraint/index.
- The second page contains exactly one WhatsApp action, built from the committed database record and complete advisory report.
- The visitor must review the WhatsApp draft and press Send inside WhatsApp; delivery is not confirmed to the website.
