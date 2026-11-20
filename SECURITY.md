# Security and limitations
- Never ask for passwords, OTPs, verification codes, recovery keys, session cookies or payment details.
- Intake uses CSRF, server-side type/length/control-character validation, HTTPS-only evidence links, consent, honeypot and a timed arithmetic challenge.
- Cookies use Secure (when configured), HttpOnly and SameSite=Lax. Admin credential comparisons use hmac.compare_digest; successful login clears the pre-authentication session.
- Responses set CSP without inline scripts, X-Content-Type-Options, X-Frame-Options, Referrer-Policy and Permissions-Policy.
- Rate limits: global 200/hour, intake POST 5/hour, admin login POST 10/hour. Default in-memory limiter resets on restart and is not multi-instance protection.
- Risk flags are text-based advisory prompts only, not proof of fraud or identity verification.
- SQLite data on Render Free is ephemeral and can be lost after restart/redeploy. This demo has no automatic deletion job despite CASE_RETENTION_DAYS; define retention before production.
- Before production use durable database/storage, backups, monitoring, shared rate-limit storage, access controls and a tested deletion process.
- Evidence links are not fetched server-side. Review untrusted links cautiously.


## WhatsApp and customer data
Case records are committed to the configured database before the WhatsApp handoff is displayed. WhatsApp is click-to-chat only; this app does not send messages through the WhatsApp Business API. On Render, configure a persistent PostgreSQL `DATABASE_URL`; SQLite on the ephemeral web-service filesystem is not durable. Back up the database and never place secrets in the repository.
