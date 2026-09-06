#!/usr/bin/env bash
# Push the deployment configuration of api/.env to the Vercel projects.
#
# Values are read straight from api/.env and the local signing material and
# piped to `vercel env add`, so no secret is ever echoed. Re-runnable: each
# variable is removed before it is re-added.
#
# Prerequisites:
#   vercel login
#   SFC_GITHUB_TOKEN=github_pat_...   (fine-grained, read-only on
#                                      liapisn/solo-founder-crew → Contents)
#
# Usage:  SFC_GITHUB_TOKEN=... ./scripts/sync_vercel_env.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$PWD
SCOPE="liap1s-projects"
API_PROJECT="passly-api"
WEB_PROJECT="passly"

# The web origin proxies /api/* to the API, so one public hostname covers both.
# Use the custom domain, not the .vercel.app alias: it is what canonical links,
# OG tags and emailed pass links are built from, and the apex 308s to www.
WEB_URL="https://www.passly.gr"
API_URL="https://passly-api.vercel.app"

[ -f api/.env ] || { echo "api/.env not found" >&2; exit 1; }
: "${SFC_GITHUB_TOKEN:?set SFC_GITHUB_TOKEN to a read-only PAT for solo-founder-crew}"

# Read one KEY=value from api/.env, ignoring comments and surrounding quotes.
from_env() {
  sed -nE "s/^$1=[\"']?(.*[^\"'])[\"']?[[:space:]]*$/\1/p" api/.env | head -1
}

# Replace a variable across all three environments of a project.
#
# `vercel env add` takes exactly one environment per call, hence the loop, and
# reads the value from stdin so it never appears in a command line (where `ps`
# would show it). --force overwrites an existing value, which is what makes
# this script re-runnable.
put() { # put <project> <name> <value>
  local project=$1 name=$2 value=$3
  for target in production preview development; do
    printf '%s' "$value" |
      vercel env add "$name" "$target" \
        --force --yes --scope "$SCOPE" --project "$project" >/dev/null
  done
  echo "  $project ← $name"
}

echo "API project ($API_PROJECT)"

# Database. The pooler host in api/.env is correct for serverless; the direct
# Supabase host is IPv6-only and unreachable from most builders. Keep the pool
# tiny — every warm instance opens its own.
put "$API_PROJECT" DATABASE_URL       "$(from_env DATABASE_URL)"
put "$API_PROJECT" PASSLY_DB_POOL_MAX "2"

# Apple Wallet signing. The .p12 and WWDR cert are gitignored, so they travel
# as base64 rather than as the repo-relative paths api/.env uses locally.
put "$API_PROJECT" APPLE_TEAM_ID       "$(from_env APPLE_TEAM_ID)"
put "$API_PROJECT" APPLE_PASS_TYPE_ID  "$(from_env APPLE_PASS_TYPE_ID)"
put "$API_PROJECT" APPLE_CERT_PASSWORD "$(from_env APPLE_CERT_PASSWORD)"
put "$API_PROJECT" APPLE_CERT_P12_B64  "$(base64 < "$ROOT/passly.p12" | tr -d '\n')"
put "$API_PROJECT" APPLE_WWDR_CERT_B64 \
  "$(base64 < "$ROOT/$(from_env APPLE_WWDR_CERT | sed 's#^\.\./##')" | tr -d '\n')"

# Email. Links point at the web origin's /api proxy, not at the API project
# directly, so a customer only ever sees one hostname.
EMAIL_FROM=$(from_env PASSLY_EMAIL_FROM)
put "$API_PROJECT" RESEND_API_KEY     "$(from_env RESEND_API_KEY)"
put "$API_PROJECT" PASSLY_EMAIL_FROM  "${EMAIL_FROM:-onboarding@resend.dev}"
put "$API_PROJECT" PASSLY_PUBLIC_URL  "$WEB_URL/api"

# Build-time only: api/vercel.json's installCommand expands this to fetch the
# private framework. requirements.txt stays clean so CI keeps installing
# without a token.
put "$API_PROJECT" SFC_GITHUB_TOKEN "$SFC_GITHUB_TOKEN"

echo "Web project ($WEB_PROJECT)"
put "$WEB_PROJECT" API_ORIGIN          "$API_URL"
put "$WEB_PROJECT" NEXT_PUBLIC_SITE_URL "$WEB_URL"

echo
echo "Done. Redeploy both projects for the new values to take effect."
