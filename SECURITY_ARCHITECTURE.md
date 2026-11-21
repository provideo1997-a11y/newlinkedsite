# YAKUZA — Security architecture and adversarial threat model

**Scope:** Flask public intake, SQLite/PostgreSQL persistence, session-authenticated admin dashboard, CSV export, and WhatsApp `wa.me` hand-off. This is a code-level design review of this repository, not a penetration test or certification.

## 1. System and trust boundaries

```text
Public browser (untrusted)
  | HTTPS / form POST / CSRF token / arithmetic challenge
  v
Render edge TLS termination
  | one trusted proxy hop (ProxyFix: x_for=1, x_proto=1)
  v
Flask application
  |-- public intake validation + honeypot + rate limiter
  |-- SQLAlchemy ORM / parameterized queries
  |-- server-side session + CSRF
  |-- admin authentication / authorization
  |-- CSV export
  v
PostgreSQL (recommended) or local SQLite (development only)

WhatsApp branch:
separate sharing consent -> case transaction committed -> complete message built
                                                        |
                                                        v
                                              single 303 redirect to WhatsApp after commit
                                                        |
                                                        v
                                                    wa.me link
                                                        |
                                                        v
                                          visitor reviews and presses Send
```

Trust boundaries:
- Public input is hostile, even after browser validation.
- `X-Forwarded-*` is trusted only for the single Render proxy hop; do not place this service behind additional proxies without recalibrating ProxyFix.
- The database is a separate trust boundary. Credentials belong only in Render environment variables.
- WhatsApp is an external service. The prefilled draft is not message delivery; the visitor must press Send. WhatsApp replies are not synchronized into the case system.
- Admin sessions are privileged. The hidden URL prefix is not an access-control mechanism.

## 2. Attacker-first threat register

Likelihood is qualitative for an internet-facing small intake service. Impact means plausible consequence if exploited.

| Threat / path | STRIDE / OWASP / ATT&CK mapping | Likelihood | Impact | Current mitigation | Residual gap |
|---|---|---:|---:|---|---|
| Bot floods intake and exhausts CPU/database | DoS; OWASP A04/A05; ATT&CK T1499 | High | Medium–High | configurable 30/hour intake limit, global defaults, honeypot, human challenge, request-size cap | `memory://` counters reset on restart and are not shared; use Redis-compatible shared storage when scaling |
| Credential stuffing against admin | Spoofing; A07; T1110 | Medium | Critical | password hashing, login rate limit, obscure route, secure session | no MFA or centralized lockout/alerting; use MFA before production |
| Stolen admin password/session | Spoofing / Elevation; A07; T1556 | Medium | Critical | HTTPOnly/SameSite/Secure cookie, 30-minute session, CSRF, server-side admin lookup | no MFA, device binding, or forced global session revocation |
| CSRF on status change/logout | Tampering; A01 | Medium | Medium | Flask-WTF CSRF tokens on forms | verify all future admin mutations retain CSRF and POST-only semantics |
| Stored XSS via complaint/name/evidence | Tampering / Information Disclosure; A03 | Medium | High | Jinja autoescaping; no raw HTML rendering; CSP; evidence link uses `noopener noreferrer` | future template filters or `safe` markup could reintroduce XSS |
| SQL injection through form/search | Tampering; A03 | Low | High | SQLAlchemy ORM and bound query parameters | keep raw SQL restricted to fixed migration statements; never interpolate user input |
| CSV formula injection by exported user fields | Tampering / Execution; A03 | Medium | High | CSV cells beginning with formula operators are prefixed before export | users still control exported content; treat exports as sensitive and open only in trusted tools |
| WhatsApp number malformed or full case data exposed in click-to-chat URL | Information Disclosure / Tampering | Medium | High | normalize `00`, `+`, separators; validate international length; separate explicit data-sharing consent; 303 redirect response uses `no-referrer`; application never logs the message URL | Full message text is intentionally sent to the WhatsApp service and may remain in browser history; minimize data, obtain consent, and never include credentials or authentication secrets |
| TOCTOU / duplicate submissions | Tampering / DoS | Medium | Medium | server-side unique case reference; 48-bit reference suffix; database uniqueness; disable repeat-click in UI | database uniqueness conflict is not retried; add retry/backoff if volume grows |
| Case data lost on restart/redeploy | Availability / Tampering | High on Free SQLite | Critical | PostgreSQL supported; deployment guide prohibits SQLite in production | Render Free Postgres expires after 30 days and has no backups; paid durable DB required |
| Malicious evidence URL / phishing | Information Disclosure / Social Engineering | Medium | Medium | HTTPS-only URL validation; no server-side fetch; new tab with `noopener` | URL is not verified as safe or authentic; staff must not download/run content blindly |
| Compromised dependency/build chain | Supply chain; A08; T1195 | Medium | High | pinned direct dependencies; GitHub-to-Render deploy | no automated dependency audit/SBOM/signature enforcement; add Dependabot and CI security checks |
| Insider exports or reads cases | Repudiation / Information Disclosure; A09 | Medium | Critical | admin-only dashboard/export; no-store headers | single admin role, no per-action audit trail, no MFA, no dual control |
| Proxy header spoofing / rate-limit identity bypass | Spoofing; A05 | Medium | Medium | ProxyFix trusts exactly one forwarded hop for Render | if proxy topology changes, client IP attribution may be wrong; verify via logs |
| Race during schema migration / multiple workers | Tampering / Availability | Low at configured 1 worker | High | single Gunicorn worker and additive migration | do not scale workers/instances before moving migrations to a controlled migration tool |

## 3. Root causes and cascading failure modes

1. **Durability is a hosting property, not a Flask setting.** A correct SQLAlchemy model cannot make Render's ephemeral filesystem durable. SQLite on a free web service can silently lose case records on spin-down/redeploy. The only sound fix is an independently durable database with backups.
2. **Rate limiting is stateful infrastructure.** `memory://` is process-local. Restarting the process resets counters; multiple instances do not share limits. It is a useful friction control, not a robust DDoS defense.
3. **A hidden admin URL is not authentication.** Discovery by crawling, logs, browser history, or referrers is plausible. Password authentication remains mandatory; MFA is the next material upgrade.
4. **WhatsApp click-to-chat URLs are browser-visible.** To meet the complete-report workflow, the URL contains the submitted contact details, incident description, and generated triage report after a separate explicit consent. It is sent to WhatsApp and may remain in browser history. The redirect response uses `Referrer-Policy: no-referrer`; application code must never log the full URL or query. Never include passwords, one-time codes, recovery keys, payment details, or identity documents.
5. **Heuristic scoring is epistemically weak.** Keyword matches can be quoted, negated, translated, or maliciously planted. The score must only prioritize human review and must never label a person as a scammer.
6. **A single admin role creates a large blast radius.** Anyone who compromises that account can view all records and export them. Add MFA, least-privilege roles, action audit logs, and export alerts before a team rollout.

## 4. Hardening roadmap

### Required before real customer data
- Connect a paid PostgreSQL database with automated backups and test a restore.
- Rotate any previously exposed `SECRET_KEY` and admin password. Remove leaked credentials from screenshots, repository history, and logs where possible.
- Set `COOKIE_SECURE=1`, a long unique `SECRET_KEY`, and a unique admin password (16+ characters).
- Add MFA for administrators (prefer TOTP or WebAuthn through a maintained identity provider).
- Define data minimization, a retention period, deletion/export process, privacy contact, and applicable legal basis.
- Add tamper-evident audit events for login success/failure, case views, status changes, and CSV exports; send logs off-host.
- Configure a shared Redis-compatible rate-limit store; keep a per-IP and per-session dimension and alert on spikes.
- Add dependency scanning and CI: `pip-audit`, `bandit`, unit tests, and a lockfile/SBOM. Review and update pins on a controlled schedule.
- Use a managed email provider for verified contact workflows if email delivery is required; Render Free web services block common SMTP ports.

### Advanced / next-generation options
- **Passkeys/WebAuthn + step-up auth for CSV export:** strongest practical improvement against stolen passwords; adds identity-provider complexity.
- **Append-only audit chain:** each audit record stores the previous event hash and its own canonical event hash; periodically anchor a signed digest outside the database. This detects later alteration but does not stop a privileged attacker from suppressing events before anchoring.
- **Object storage quarantine for future attachments:** upload to a private bucket, random object key, strict size/type allowlist, malware scanning in an isolated worker, and short-lived signed download URLs. Do not accept direct file uploads until this pipeline exists.
- **Risk-adaptive rate limiting:** increase friction on bursts, repeated failed arithmetic checks, invalid CSRF, and repeated login failures. Avoid aggressive fingerprinting that creates privacy or false-positive problems.
- **Formal invariants / property-based tests:** verify that every accepted case has a unique reference, unauthenticated clients cannot reach admin routes, no redirect occurs before database commit, and CSV cells cannot become spreadsheet formulas.
- **Moving-target defense:** rotate admin URL prefix only as supplemental friction; it must never replace authentication, MFA, and monitoring.

## 5. Telemetry and containment

Emit structured, privacy-minimized events:
- `intake.accepted` (case reference, timestamp, urgency, platform; do not duplicate full narrative)
- `intake.rejected` (reason code, request ID; never log raw secrets or full form payload)
- `auth.login_success` / `auth.login_failure` (admin ID if known, source IP, user agent hash, timestamp)
- `admin.case_view`, `admin.case_status_changed`, `admin.csv_export`
- `whatsapp.redirect_created` (case reference only; never log full URL query)
- `database.error`, `rate_limit.triggered`, `health.failure`

High-signal alerts:
- 5+ failed admin logins in 10 minutes from one source or across many usernames.
- CSV export outside expected hours or repeated exports in a short window.
- sudden intake rate increase, repeated invalid human checks, or a high ratio of rejected requests.
- unexpected admin path changes, repeated 401/403/404 probes, database connection failures, or case count drops.
- a spike in status changes or bulk case access.

Containment:
- **Credential incident:** rotate `ADMIN_PASSWORD` and `SECRET_KEY`; revoke active sessions by rotating `SECRET_KEY`; inspect exports and case access.
- **Spam/DoS:** temporarily disable public POST intake using a maintenance flag, preserve GET/read-only admin access, and increase edge/WAF controls.
- **Database compromise:** restrict network credentials, take a forensic snapshot, rotate credentials, restore to a clean instance, and notify affected parties as required.
- **WhatsApp misconfiguration:** reject the submission before commit when `WHATSAPP_NUMBER` is missing or invalid; no case is committed and no external redirect occurs.

## 6. Engineering trade-offs

| Control | Security benefit | Cost / UX trade-off |
|---|---|---|
| Shared Redis rate limits | Consistent limits across restarts/instances | Extra service and credentials; free volatile KV is not durable |
| MFA / passkeys | Strong reduction in account takeover risk | Setup friction and recovery support |
| Paid PostgreSQL + backups | Durable records and recoverability | Monthly cost and restore operations |
| External audit sink | Better tamper resistance and incident visibility | More integration and log-retention cost |
| File quarantine/scanning | Reduces malicious upload risk | Latency, storage, worker complexity |
| Adaptive challenges | Better bot resistance than fixed arithmetic | False positives and accessibility burden |

## 7. Explicit non-goals and limits

- No automated account takeover, password collection, OTP collection, bypass of platform controls, or impersonation.
- No external verification of evidence, identity, scam claims, or platform account ownership.
- No automatic WhatsApp reply ingestion.
- No guarantee of account restoration, fraud finding, or permanent uptime on a free hosting plan.
- No claim that a code review is a penetration test.

## 8. Validation checklist

Run after each deployment:
1. `/health` returns 200.
2. Public intake rejects missing CSRF, invalid arithmetic answer, missing authorization, invalid email, invalid evidence URL, and honeypot completion.
3. A valid dummy report creates one case with one unique reference.
4. The visitor activates the form’s sole **Send to WhatsApp** button. The same-origin request must receive a successful response only after the server commits the case; the browser then navigates to the validated full prefilled WhatsApp message. The no-JavaScript path receives a 303 only after commit. The visitor must still press Send manually inside WhatsApp.
5. `0049...`, `+49...`, and `49...` produce the same `wa.me` number; malformed numbers do not redirect.
6. WhatsApp draft is generated only after the database commit, requires explicit sharing consent, and contains the case reference, submitted fields, full description, and triage report. The visitor must press Send manually.
7. Anonymous requests to every admin route are redirected to login.
8. Admin language selection persists after login, and RTL is applied for Arabic.
9. Status updates require POST + CSRF and persist after refresh.
10. CSV cells starting with `=`, `+`, `-`, and `@` are neutralized.
11. Restart/redeploy does not lose records when connected to the intended production database.
12. A backup is restored into a separate test database successfully.


## Final submission reliability controls
The application has one public case submission action. The browser POST uses JSON and refuses automatic redirect following; it only navigates after validating the successful server response and the `https://wa.me/<digits>` destination. The no-JavaScript path still redirects only after commit. Signed per-form references make retry idempotent, unique constraints handle simultaneous duplicate requests, PostgreSQL connection/pool/statement/lock waits and SQLite lock waits are bounded, `/health/db` checks database reachability, and support-reference logs identify the failing stage without including submitted PII. The complete message URL is treated as sensitive; responses are no-store and use `Referrer-Policy: no-referrer`. A normal `wa.me` link cannot press Send or confirm delivery.
