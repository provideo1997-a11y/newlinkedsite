#!/usr/bin/env bash
set -euo pipefail

# Run from the root of the existing newlinkedsite Git repository after extracting
# this release into that repository root.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Error: run this script from inside the existing Git repository." >&2
  exit 1
}
cd "$ROOT"

FILES=(
  .env.example .gitignore APPLY_UPDATE.md BUILD_VERIFICATION.md CHANGELOG_FINAL.md
  COMMIT_UPDATE.sh COMMIT_UPDATE.ps1 FREE_HOSTING_AND_DOMAIN_GUIDE.md
  Procfile README.md RENDER_FREE_LIMITS.md SECURITY_ARCHITECTURE.md
  TECHNICAL_REVIEW.md app.py render.yaml requirements.txt runtime.txt
  security_utils.py pytest.ini
  static/css/style.css static/img/mark.svg static/img/yakuza-network.webp
  static/img/yakuza-shield.webp static/js/app.js
  templates/about.html templates/admin.html templates/admin_login.html
  templates/base.html templates/case_detail.html templates/contact.html
  templates/index.html templates/privacy.html templates/services.html
  templates/submitted.html
  tests/conftest.py tests/test_security_utils.py tests/test_translation_catalog.py
)

git add -- "${FILES[@]}"
git diff --cached --check
echo "Staged project update:"
git diff --cached --stat

git commit -m "Fix YAKUZA startup, PostgreSQL and admin translations"
git push origin HEAD
