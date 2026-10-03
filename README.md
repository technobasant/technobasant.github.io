# Basant Bhattarai — Personal site

Staff-level portfolio for a Senior Data & AI Engineer / platform architect.  
Live: [basantbhattarai.com.np](https://basantbhattarai.com.np)

## Principles

- Authority over decoration — outcomes and ownership, not tool laundry lists
- ClickHomes appears only under **Work** (`/projects/`)
- Consulting availability is on **About** only — not the landing page
- CV source of truth: `cv/` (local copy of `realestate/cv/`; not committed, because this repo is public and the seeds carry employer detail)
- Job apply agent (standalone): `/Users/basant/personal_projects/job-apply-agent`

## Local

```bash
cd technobasant.github.io

# If native gems fail (missing iostream), set C++ includes first:
export SDKROOT="$(xcrun --show-sdk-path)"
export CPLUS_INCLUDE_PATH="${SDKROOT}/usr/include/c++/v1"

bundle install
bundle exec jekyll serve
# → http://127.0.0.1:4000
```

Or: `./scripts/serve.sh`

## Structure

| Path | Role |
|------|------|
| `_layouts/` | `default`, `home`, `page` |
| `assets/css/site.css` | Dark editorial design system |
| `_pages/` | About, Experience, Skills, Work |
| `_posts/` | Published essays and reproducible tutorials |
| `_drafts/` | Unfinished outlines; excluded from the default preview |
| `scripts/gen-cover-diagram.py` | Schematic cover masters; `python3 scripts/gen-cover-diagram.py <name>` |

`make serve` previews the same finished writing readers will see. Use
`make serve-drafts` only while editing unfinished outlines.

Pieces drawn from employer production work go in the `production-notes`
series and are published only once cleared. They describe mechanisms, staging
measurements and ratios — never customer data, internal scale or identifiers
(`rake privacy` and the boundary stated in `llms.txt`). Uncleared pieces wait
in `_drafts/`.

Run `make content` before publishing, then push `master` to publish on GitHub
Pages.

Use `make new-post SLUG=... TITLE="..."` for an essay and
`make new-tutorial SLUG=... TITLE="..."` for a reproducible runbook. The two
templates carry separate editorial contracts so tutorial steps, evidence, and
failure boundaries do not collapse into generic prose.
