# Render Free: availability and data durability

Render's current Free plan has limitations that conflict with the requirement for a permanent case-management service:

- Free web services spin down after 15 minutes without inbound traffic and usually take about a minute to wake.
- The local filesystem is ephemeral. SQLite records stored in the service filesystem can disappear on restart, redeploy, or spin-down.
- Free Render Postgres expires 30 days after creation, has no backups, and is not permanent.
- Free services may restart and do not support persistent disks.
- Render describes Free instances as suitable for testing/hobby use, not production.

Consequences:
- You can keep the public demo running on Free, but it will not be always-on.
- You must not treat SQLite on Render as permanent storage.
- Free Postgres is temporary; plan an upgrade before expiry and configure backups.
- For real client/case data, use paid PostgreSQL with backups and a paid always-on web service, or a separate provider offering durable storage and availability.
- If you must stay at $0, use this build only with dummy/test data and export/backup frequently. There is no honest configuration that makes Render Free permanently durable.

Official references:
- https://render.com/docs/free
- https://render.com/docs/your-first-deploy
