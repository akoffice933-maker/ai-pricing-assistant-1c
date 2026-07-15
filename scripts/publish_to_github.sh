#!/usr/bin/env bash
set -euo pipefail

# Safe GitHub publish script.
# It does NOT store the token in git config or files.
# Usage:
#   export GITHUB_TOKEN="<new-token>"
#   export GITHUB_OWNER="your-login-or-org"
#   export GITHUB_REPO="ai-pricing-assistant-1c"
#   export GITHUB_VISIBILITY="public"   # or private
#   ./scripts/publish_to_github.sh

: "${GITHUB_TOKEN:?Set GITHUB_TOKEN in environment. Do not put it into files.}"
: "${GITHUB_OWNER:?Set GITHUB_OWNER in environment.}"
GITHUB_REPO="${GITHUB_REPO:-ai-pricing-assistant-1c}"
GITHUB_VISIBILITY="${GITHUB_VISIBILITY:-public}"

if [[ "$GITHUB_VISIBILITY" != "public" && "$GITHUB_VISIBILITY" != "private" ]]; then
  echo "GITHUB_VISIBILITY must be public or private" >&2
  exit 1
fi

PRIVATE_JSON="false"
if [[ "$GITHUB_VISIBILITY" == "private" ]]; then
  PRIVATE_JSON="true"
fi

DESCRIPTION="AI Pricing Assistant for 1C: market-aware demand curve forecasting and price optimization with FastAPI skills layer and 1C integration skeleton."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "Initial commit: AI Pricing Assistant for 1C"
fi

# Create repository. If it already exists, continue.
CREATE_RESPONSE="$({
  curl -sS -w "\n%{http_code}" -X POST "https://api.github.com/user/repos" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -d "{\"name\":\"${GITHUB_REPO}\",\"description\":\"${DESCRIPTION}\",\"private\":${PRIVATE_JSON},\"has_issues\":true,\"has_projects\":true,\"has_wiki\":true}"
} || true)"

HTTP_CODE="$(echo "$CREATE_RESPONSE" | tail -n1)"
BODY="$(echo "$CREATE_RESPONSE" | sed '$d')"

if [[ "$HTTP_CODE" == "201" ]]; then
  echo "Repository created: ${GITHUB_OWNER}/${GITHUB_REPO}"
elif [[ "$HTTP_CODE" == "422" ]]; then
  echo "Repository may already exist: ${GITHUB_OWNER}/${GITHUB_REPO}"
else
  echo "GitHub API returned HTTP ${HTTP_CODE}" >&2
  echo "$BODY" >&2
  exit 1
fi

REMOTE_URL="https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

# Push using an in-memory auth header. Token is not saved in remote URL.
git -c http.extraHeader="Authorization: Bearer ${GITHUB_TOKEN}" push -u origin main

echo "Published: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}"
