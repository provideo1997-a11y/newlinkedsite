$ErrorActionPreference = 'Stop'
git rev-parse --show-toplevel *> $null
if ($LASTEXITCODE -ne 0) { throw 'Run this script inside the existing Git repository.' }
$trackedEnv = git ls-files | Where-Object { $_ -match '^\.env($|\.)' -and $_ -ne '.env.example' }
if ($trackedEnv) { throw "Refusing to stage tracked environment secrets: $($trackedEnv -join ', '). Untrack them and rotate exposed secrets first." }
$trackedData = git ls-files -- 'instance/**' '*.db' '*.sqlite' '*.sqlite3'
if ($trackedData) { throw 'Refusing to stage: database/instance files are tracked. Back them up and remove from Git index/history first.' }
git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Staged diff check failed.' }
Write-Host "Target branch: $(git branch --show-current)"
git diff --cached --stat
git status --short
$answer = Read-Host 'Type COMMIT to create and push this change'
if ($answer -cne 'COMMIT') { throw 'Cancelled; staged changes were left for review.' }
git commit -m "Fix YAKUZA WhatsApp intake and full case hand-off"
if ($LASTEXITCODE -ne 0) { throw 'Commit failed. Review staged changes.' }
git push origin HEAD
if ($LASTEXITCODE -ne 0) { throw 'Push failed. Check your current branch upstream and GitHub authentication.' }
