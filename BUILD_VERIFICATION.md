# Build verification — CSRF / reload repair

## Verified in this build environment
- `pytest -q`: **46 passed**.
- Python bytecode compilation and AST parsing: passed.
- JavaScript syntax (`node --check static/js/app.js`): passed.
- All 9 Jinja templates parsed: passed.
- Contact form has exactly one submit button and an explicit canonical `/contact` action.
- CSRF error response returns fresh CSRF/case tokens and no reload directive.
- Client retries one recoverable CSRF failure in-place and contains no `window.location.reload()` call.
- Existing WhatsApp link/message generation, case idempotency, migration, database timeout, translation, and security tests passed.
- Release ZIP integrity and SHA-256 verified.

## Not verified here
The environment has no Flask / Flask-SQLAlchemy / Flask-WTF / Flask-Limiter packages and cannot resolve the package index or your Render host. Therefore, this environment could not run the full Flask HTTP test client against PostgreSQL or perform a live WhatsApp hand-off. Do a dummy-case staging submission after deployment and check `FINAL_DEPLOYMENT_DIAGNOSTICS.md` before accepting real requests.
