#!/usr/bin/env bash
# Align Cloudflare bot/WAF settings with public-site SEO + AI Overviews.
#
# This zone is GitHub Pages behind DNS-only records. WAF/Bot Fight Mode do not
# see traffic unless records are later proxied (orange cloud). The settings
# below still matter: Cloudflare's 15 Sep 2026 defaults will block mixed-purpose
# crawlers (Googlebot, Bingbot, Applebot) if "Block AI bots" / Training-block
# is on *and* the hostname is proxied.
#
# Required token permissions (current DNS token is not enough):
#   Zone.Zone Read, Zone.Bot Management Write, Zone.WAF Write, Zone.Zone Settings Write
#
#   scripts/cloudflare-allow-crawlers.sh
#
# Reads CLOUDFARE_API_TOKEN (or CLOUDFLARE_API_TOKEN) from .env. Never prints it.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

TOKEN="${CLOUDFARE_API_TOKEN:-${CLOUDFLARE_API_TOKEN:-}}"
ZONE_NAME="${CLOUDFLARE_ZONE:-basantbhattarai.com.np}"

if [[ -z "$TOKEN" ]]; then
  echo "CLOUDFARE_API_TOKEN is not set (put it in .env)." >&2
  exit 1
fi

api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -sS -X "$method" "https://api.cloudflare.com/client/v4${path}" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      --data "$body"
  else
    curl -sS -X "$method" "https://api.cloudflare.com/client/v4${path}" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json"
  fi
}

zone_json="$(api GET "/zones?name=${ZONE_NAME}")"
zid="$(python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result") or [];
print(r[0]["id"] if r else "")' <<<"$zone_json")"
if [[ -z "$zid" ]]; then
  echo "Could not find zone ${ZONE_NAME}." >&2
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("errors") or d.get("messages") or "no zone")' <<<"$zone_json" >&2
  exit 1
fi

python3 - <<'PY' "$TOKEN" "$zid" "$ZONE_NAME"
import json, sys, urllib.request, urllib.error

token, zid, zone_name = sys.argv[1], sys.argv[2], sys.argv[3]
base = f"https://api.cloudflare.com/client/v4/zones/{zid}"

def call(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"success": False, "errors": [{"message": raw[:240]}]}
        return e.code, parsed

def err_msg(payload):
    errs = payload.get("errors") or []
    if not errs:
        return payload.get("messages") or payload
    return "; ".join(e.get("message", str(e)) for e in errs)

print(f"zone {zone_name}")

status, dns = call("GET", "/dns_records?per_page=100")
if status != 200 or not dns.get("success"):
    print(f"  DNS read failed ({status}): {err_msg(dns)}")
    sys.exit(1)

records = [
    r for r in (dns.get("result") or [])
    if r.get("type") in {"A", "AAAA", "CNAME"}
]
proxied = [r for r in records if r.get("proxied")]
dns_only = [r for r in records if not r.get("proxied")]
print(f"  HTTP records: {len(records)}  proxied={len(proxied)}  dns-only={len(dns_only)}")
for r in records:
    print(f"    {r['type']:5} {r['name']}  proxied={r.get('proxied')}")

if not proxied:
    print("  Traffic does not pass through Cloudflare. Bot Fight Mode, Block AI Bots,")
    print("  and WAF rules cannot block Googlebot / Bingbot / AIO crawlers today.")
    print("  Keep these records DNS-only unless you also allow those crawlers first.")

# Bot Fight Mode + Block AI Bots. Disabled = allow search, Copilot, ChatGPT,
# Gemini grounding, and training crawlers that robots.txt already allows.
print("bot_management")
status, current = call("GET", "/bot_management")
if status == 403:
    print("  token cannot read Bot Management (need Zone.Bot Management Write).")
    print("  Dashboard: Security > Settings > Configure AI bot policies")
    print("    Search = Allow, Agent = Allow, Training = Allow")
    print("    Bot Fight Mode = Off  (challenges unknown crawlers, including some AIO bots)")
    print("    Managed robots.txt = Off  (this repo already ships robots.txt)")
    print("    Block AI bots / crawler link-maze = Off")
    print("  Also turn off the 15 Sep 2026 default that would block mixed-purpose")
    print("  crawlers (Googlebot, Bingbot, Applebot) if Training is set to Block.")
else:
    result = (current.get("result") or {}) if current.get("success") else {}
    if result:
        keep = {
            "ai_bots_protection": result.get("ai_bots_protection"),
            "crawler_protection": result.get("crawler_protection"),
            "content_bots_protection": result.get("content_bots_protection"),
            "fight_mode": result.get("fight_mode"),
            "is_robots_txt_managed": result.get("is_robots_txt_managed"),
        }
        print(f"  before {keep}")
    desired = {
        "ai_bots_protection": "disabled",
        "crawler_protection": "disabled",
        "content_bots_protection": "disabled",
        "cf_robots_variant": "off",
        "is_robots_txt_managed": False,
        "fight_mode": False,
    }
    put_status, put_body = call("PUT", "/bot_management", desired)
    if put_status == 200 and put_body.get("success"):
        after = put_body.get("result") or {}
        print("  updated", {
            "ai_bots_protection": after.get("ai_bots_protection"),
            "crawler_protection": after.get("crawler_protection"),
            "content_bots_protection": after.get("content_bots_protection"),
            "fight_mode": after.get("fight_mode"),
            "is_robots_txt_managed": after.get("is_robots_txt_managed"),
        })
    else:
        print(f"  update failed ({put_status}): {err_msg(put_body)}")

SKIP_DESC = "Allow search engines and AI overview crawlers"
SKIP_EXPR = " or ".join(
    [
        '(cf.verified_bot_category eq "Search Engine Crawler")',
        '(cf.verified_bot_category eq "AI Search")',
        '(cf.verified_bot_category eq "AI Crawler")',
        '(cf.verified_bot_category eq "AI Assistant")',
        '(http.user_agent contains "Googlebot")',
        '(http.user_agent contains "bingbot")',
        '(http.user_agent contains "Bingbot")',
        '(http.user_agent contains "DuckDuckBot")',
        '(http.user_agent contains "GPTBot")',
        '(http.user_agent contains "ChatGPT-User")',
        '(http.user_agent contains "OAI-SearchBot")',
        '(http.user_agent contains "ClaudeBot")',
        '(http.user_agent contains "Claude-SearchBot")',
        '(http.user_agent contains "Claude-User")',
        '(http.user_agent contains "PerplexityBot")',
        '(http.user_agent contains "Google-Extended")',
        '(http.user_agent contains "Google-CloudVertexBot")',
        '(http.user_agent contains "Applebot")',
        '(http.user_agent contains "Amazonbot")',
    ]
)
skip_rule = {
    "description": SKIP_DESC,
    "expression": SKIP_EXPR,
    "action": "skip",
    "action_parameters": {
        "phases": [
            "http_ratelimit",
            "http_request_firewall_managed",
            "http_request_sbfm",
        ]
    },
    "enabled": True,
}

print("waf skip rule")
status, entry = call("GET", "/rulesets/phases/http_request_firewall_custom/entrypoint")
if status == 403:
    print("  token cannot read WAF (need Zone.WAF Write).")
    print("  Dashboard: Security > Security rules > Custom rules")
    print(f"    description: {SKIP_DESC}")
    print("    action: Skip (WAF, rate limit, Super Bot Fight Mode)")
    sys.exit(0)

rules = []
ruleset_ok = status == 200 and entry.get("success")
if ruleset_ok:
    rules = list((entry.get("result") or {}).get("rules") or [])
elif status not in (404, 200):
    print(f"  read failed ({status}): {err_msg(entry)}")
    sys.exit(0)

kept = [r for r in rules if r.get("description") != SKIP_DESC]
# Existing skip fields from GET include ids; drop read-only keys when rewriting.
normalized = []
for r in kept:
    item = {
        "description": r.get("description"),
        "expression": r.get("expression"),
        "action": r.get("action"),
        "enabled": r.get("enabled", True),
    }
    if r.get("id"):
        item["id"] = r["id"]
    if r.get("action_parameters"):
        item["action_parameters"] = r["action_parameters"]
    normalized.append(item)
normalized.insert(0, skip_rule)

put_status, put_body = call(
    "PUT",
    "/rulesets/phases/http_request_firewall_custom/entrypoint",
    {"rules": normalized},
)
if put_status == 200 and put_body.get("success"):
    print(f"  upserted skip rule ({len(normalized)} custom rule(s) total)")
else:
    print(f"  update failed ({put_status}): {err_msg(put_body)}")
PY
