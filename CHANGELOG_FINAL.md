# Final reliability repair changelog

## Submission and WhatsApp hand-off

- Preserved the single **Send to WhatsApp** action and removed receipt/secondary delivery actions.
- The browser sends one same-origin request, waits for the server's committed-case JSON response, validates the exact WhatsApp destination host/path, then opens the chat in the same tab.
- The fetch request now refuses redirects. A server-side 303 cannot be followed invisibly inside a background request and mistaken for a failed JSON response.
- The non-JavaScript form path still receives a 303 only after a successful commit.
- The prefilled WhatsApp message includes case metadata, requester details, the original report, risk indicators and triage report.

## Reliability and observability

- Added bounded PostgreSQL connection, pool, statement, and lock waits; bounded SQLite lock wait.
- Added a signed, time-limited, per-form case reference and duplicate recovery for retries and concurrent submission races.
- Added a 120-second browser deadline and intermediate accessible waiting feedback; the spinner is removed after 8 seconds if the server is still working.
- Added `/health/db` to test a simple database query independently of the basic process health endpoint.
- Added a random support reference and phase-based diagnostic log events. Logs omit report content and contact fields.
- Improved visible handling of server error status codes and support references.

## Verification boundaries

Thirty-nine source/unit tests, Python compilation, JavaScript syntax, template parsing, YAML parsing and shell syntax checks pass. Full Flask integration, production PostgreSQL, Render and device-level WhatsApp delivery could not be run in this environment. See `BUILD_VERIFICATION.md` and `FINAL_DEPLOYMENT_DIAGNOSTICS.md`.
