$ErrorActionPreference = 'Stop'

git rev-parse --show-toplevel *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Run this script from inside the existing Git repository.'
}

$files = @(
    '.env.example', '.gitignore', 'APPLY_UPDATE.md', 'BUILD_VERIFICATION.md', 'CHANGELOG_FINAL.md',
    'COMMIT_UPDATE.sh', 'COMMIT_UPDATE.ps1', 'FREE_HOSTING_AND_DOMAIN_GUIDE.md',
    'Procfile', 'README.md', 'RENDER_FREE_LIMITS.md', 'SECURITY_ARCHITECTURE.md',
    'TECHNICAL_REVIEW.md', 'app.py', 'render.yaml', 'requirements.txt',
    'runtime.txt', 'security_utils.py', 'pytest.ini',
    'static/css/style.css', 'static/img/mark.svg', 'static/img/yakuza-network.webp',
    'static/img/yakuza-shield.webp', 'static/js/app.js',
    'templates/about.html', 'templates/admin.html', 'templates/admin_login.html',
    'templates/base.html', 'templates/case_detail.html', 'templates/contact.html',
    'templates/index.html', 'templates/privacy.html', 'templates/services.html',
    'templates/submitted.html',
    'tests/conftest.py', 'tests/test_security_utils.py', 'tests/test_translation_catalog.py'
)

git add -- $files
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Staged diff check failed.' }
git diff --cached --stat

git commit -m "Fix YAKUZA startup, PostgreSQL and admin translations"
if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }
git push origin HEAD
if ($LASTEXITCODE -ne 0) { throw 'git push failed. Check the current branch upstream and authentication.' }
