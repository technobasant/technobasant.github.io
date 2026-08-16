# Basant Bhattarai — Personal site

Staff-level portfolio for a Senior Data & AI Engineer / platform architect.  
Live: [basantbhattarai.com.np](https://basantbhattarai.com.np)

## Principles

- Authority over decoration — outcomes and ownership, not tool laundry lists
- ClickHomes appears only under **Work** (`/projects/`)
- Consulting availability is on **About** only — not the landing page
- CV source of truth: `realestate/cv/` (kept out of this repo)

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

`make serve` previews the same finished writing readers will see. Use
`make serve-drafts` only while editing unfinished outlines.

Run `make content` before publishing, then push `master` to publish on GitHub
Pages.

Use `make new-post SLUG=... TITLE="..."` for an essay and
`make new-tutorial SLUG=... TITLE="..."` for a reproducible runbook. The two
templates carry separate editorial contracts so tutorial steps, evidence, and
failure boundaries do not collapse into generic prose.
