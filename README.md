# Basant Bhattarai — Personal site

Staff-level portfolio for a Senior Data & AI Engineer / platform architect.  
Live: [technobasant.github.io](https://technobasant.github.io)

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
| `_posts/` | Occasional notes |

Push `master` to publish on GitHub Pages.
