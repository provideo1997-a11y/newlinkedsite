#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "Run inside the existing Git repository." >&2; exit 1; }
cd "$ROOT"
tracked_env_files="$(git ls-files | grep -E '^\.env($|\.)' | grep -v '^\.env\.example$' || true)"
if [[ -n "$tracked_env_files" ]]; then
  echo "Refusing to stage tracked environment secrets:\n$tracked_env_files" >&2
  echo "Untrack those files and rotate any exposed secrets before continuing." >&2
  exit 1
fi
if git ls-files -- 'instance/**' '*.db' '*.sqlite' '*.sqlite3' | grep -q .; then
  echo "Refusing to stage: database/instance files are tracked. Remove them from Git history/index after backing them up." >&2
  exit 1
fi
git add -A
git diff --cached --check
echo "Target branch: $(git branch --show-current)"
echo "Review the full replacement below. Confirm no secrets or unrelated files are staged:"
git diff --cached --stat
git status --short
printf '\nType COMMIT to create and push this change: '
read -r answer
[[ "$answer" == "COMMIT" ]] || { echo "Cancelled; staged changes were left for review."; exit 1; }
git commit -m "Refresh YAKUZA UI, accessibility and case workflows"
git push origin HEAD
