# Apply the complete replacement

1. Back up the repository and database.
2. Extract this ZIP. Copy the project contents into the repository root, replacing source files.
3. Preserve `.git/`, `.env`, database backups, and private uploads.
4. Confirm `app.py`, `requirements.txt`, `render.yaml`, `templates/`, `static/`, and `tests/` are at the repository root.
5. Commit and push to the branch connected to Render.
6. Keep the existing stable `SECRET_KEY`, `DATABASE_URL`, and `WHATSAPP_NUMBER` settings. Do not rotate `SECRET_KEY` during the deployment.
7. After deployment, run one dummy case. It should POST to `/contact`, show `/case/ready/<signed-token>`, then open the prepared WhatsApp message only when the visitor clicks the second-page button.

## Render

Build command: `pip install -r requirements.txt`

Start command: `gunicorn --workers 1 --threads 4 --timeout 60 app:app`

Root directory: blank when `app.py` is at repository root.
