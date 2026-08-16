#!/usr/bin/env bash
# Notify Bing of live URLs. Follows Bing Webmaster Guidelines §§3–4 and §9:
# submit the sitemap, stream only URLs that currently return 200, never submit
# a 404.
#
#   scripts/bing-notify.sh                  # sitemap + homepage
#   scripts/bing-notify.sh --writing        # sitemap + every live /writing/ article
#   scripts/bing-notify.sh --all            # sitemap + every live indexable URL
#   scripts/bing-notify.sh https://…/path/  # plus specific URLs
#
# Reads BING_WEBMASTER_API_KEY from .env. Prints HTTP codes only — never the key.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

SITE="${SITE_URL:-https://basantbhattarai.com.np}"
SITE="${SITE%/}"

if [[ -z "${BING_WEBMASTER_API_KEY:-}" ]]; then
  echo "BING_WEBMASTER_API_KEY is not set (put it in .env)." >&2
  exit 1
fi

OUT=/tmp/bing-webmaster.out

bing_get() {
  local method="$1"
  shift
  curl -sS -o "$OUT" -w '%{http_code}' \
    --get "https://ssl.bing.com/webmaster/api.svc/json/${method}" \
    --data-urlencode "apikey=${BING_WEBMASTER_API_KEY}" \
    "$@"
}

bing_post() {
  local method="$1"
  local body="$2"
  # apikey is a query parameter. Do not use curl -G here: that would also move
  # the JSON body onto the query string.
  curl -sS -o "$OUT" -w '%{http_code}' \
    -X POST "https://ssl.bing.com/webmaster/api.svc/json/${method}?apikey=${BING_WEBMASTER_API_KEY}" \
    -H 'Content-Type: application/json; charset=utf-8' \
    --data "$body"
}

echo "GetUserSites"
code="$(bing_get GetUserSites)"
# Url + IsVerified only. The payload also carries DNS/auth challenge codes.
sites="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])).get("d") or []; print(", ".join("%s verified=%s" % (s.get("Url"), s.get("IsVerified")) for s in d))' "$OUT" 2>/dev/null || echo "(response omitted)")"
echo "  HTTP ${code}  ${sites}"

echo "GetUrlSubmissionQuota"
code="$(bing_get GetUrlSubmissionQuota --data-urlencode "siteUrl=${SITE}")"
echo "  HTTP ${code}  $(tr -d '\n' < "$OUT")"

echo "SubmitFeed ${SITE}/sitemap.xml"
code="$(bing_post SubmitFeed "{\"siteUrl\":\"${SITE}\",\"feedUrl\":\"${SITE}/sitemap.xml\"}")"
echo "  HTTP ${code}  $(tr -d '\n' < "$OUT")"

submit_url() {
  local url="$1"
  local tmp="/tmp/bing-url-body"
  local status
  status="$(curl -sS -L -o "$tmp" -w '%{http_code}' -A 'Mozilla/5.0' --max-time 20 "$url")"
  if [[ "$status" != "200" ]]; then
    echo "  skip ${url} (live HTTP ${status} — not submitting a miss)"
    return 0
  fi
  if grep -qi 'name="robots"[^>]*noindex' "$tmp"; then
    echo "  skip ${url} (noindex)"
    return 0
  fi
  local code
  code="$(bing_post SubmitUrl "{\"siteUrl\":\"${SITE}\",\"url\":\"${url}\"}")"
  echo "  HTTP ${code}  ${url}  $(tr -d '\n' < "$OUT")"
}

WRITING=0
ALL=0
EXTRA=()
for arg in "$@"; do
  case "$arg" in
    --writing) WRITING=1 ;;
    --all) ALL=1 ;;
    *) EXTRA+=("$arg") ;;
  esac
done

sitemap_locs() {
  python3 - "$SITE" "$1" <<'PY'
import sys, urllib.request, xml.etree.ElementTree as ET
site, mode = sys.argv[1].rstrip("/"), sys.argv[2]
raw = urllib.request.urlopen(site + "/sitemap.xml", timeout=30).read()
root = ET.fromstring(raw)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
for loc in root.findall(".//sm:loc", ns):
    url = (loc.text or "").strip()
    if not url:
        continue
    if mode == "writing":
        if not url.startswith(site + "/writing/"):
            continue
        if "/writing/tags" in url or "/writing/feed" in url:
            continue
    print(url)
PY
}

if [[ "$ALL" -eq 1 ]]; then
  while IFS= read -r u; do
    [[ -n "$u" ]] && EXTRA+=("$u")
  done < <(sitemap_locs all)
elif [[ "$WRITING" -eq 1 ]]; then
  while IFS= read -r u; do
    [[ -n "$u" ]] && EXTRA+=("$u")
  done < <(sitemap_locs writing)
fi

echo "SubmitUrl (200s, not noindex)"
if [[ "$ALL" -eq 0 && "$WRITING" -eq 0 && ${#EXTRA[@]} -eq 0 ]]; then
  submit_url "${SITE}/"
fi
if ((${#EXTRA[@]} > 0)); then
  echo "  ${#EXTRA[@]} candidate URL(s)"
  for url in "${EXTRA[@]}"; do
    submit_url "$url"
  done
fi
