# technobasant.github.io
#
#   make serve        production-shaped local preview (future posts + livereload)
#   make serve-drafts editorial preview including unfinished drafts
#   make build        production build, same flags as CI
#   make content      validate published post metadata and editorial structure
#   make privacy      reject confidential architecture, figures and retired routes
#   make check        html-proofer, internal only
#   make verify       output assertions against _site
#   make lighthouse   production build, then a clean server for auditing
#   make vr-accept    capture the visual-regression baseline
#   make vr           compare the running site against that baseline
#   make images       regenerate portrait derivatives, icons and social cards
#   make resume-pdf   regenerate the privacy-safe downloadable résumé
#   make new-post SLUG=my-slug TITLE="My title"
#   make new-tutorial SLUG=my-slug TITLE="My title"
#   make clean

SHELL   := /usr/bin/env bash
BUNDLE  := bundle exec
PORT    ?= 4000
# Playwright is a global install, not a project dependency — there is no
# package.json here on purpose. Homebrew's prefix first, then a plain `npm i -g`
# home, so this resolves on either setup.
NODE_PATH ?= /opt/homebrew/lib/node_modules:$(HOME)/node_modules
# `date` on macOS has no --iso-8601; this format matches the contract exactly.
NOW     := $(shell TZ=Asia/Kathmandu date '+%Y-%m-%d %H:%M:%S %z')
TODAY   := $(shell TZ=Asia/Kathmandu date '+%Y-%m-%d')

.PHONY: help serve serve-drafts build content privacy check check-external verify jsonld lighthouse vr vr-accept images resume-pdf new-post new-tutorial new-work clean

help:
	@grep -E '^#   ' $(MAKEFILE_LIST) | sed 's/^#   //'

# --future is mandatory: _config.yml sets `future: false` with
# `timezone: Asia/Kathmandu` (+0545), so a post dated later today is silently
# dropped from a local build and you spend an hour wondering where it went.
serve:
	$(BUNDLE) jekyll serve --future --livereload --port $(PORT)

serve-drafts:
	$(BUNDLE) jekyll serve --drafts --future --livereload --port $(PORT)

build:
	JEKYLL_ENV=production $(BUNDLE) jekyll build --strict_front_matter --trace

content:
	$(BUNDLE) rake content

privacy:
	$(BUNDLE) rake privacy

check:
	$(BUNDLE) rake check

check-external:
	$(BUNDLE) rake check:external

verify:
	$(BUNDLE) rake verify

jsonld:
	$(BUNDLE) rake jsonld

# livereload injects a websocket client into every page, which costs real points
# on the Lighthouse performance audit. Build production first, then serve the
# already-built _site with --skip-initial-build and no livereload.
lighthouse: build
	@echo "Serving the production build on http://127.0.0.1:$(PORT) (Ctrl-C to stop)."
	@echo "In another terminal, run:"
	@echo
	@echo "  npx --yes lighthouse http://127.0.0.1:$(PORT)/ \\"
	@echo "    --preset=desktop --only-categories=performance,accessibility,best-practices,seo \\"
	@echo "    --chrome-flags='--headless=new' --view"
	@echo
	JEKYLL_ENV=production $(BUNDLE) jekyll serve --skip-initial-build --no-watch --port $(PORT)

# Visual regression. Refactors that are supposed to be inert — deleting an
# unreachable rule, folding an override into its base — are gated at zero
# differing pixels. Needs a server already running on $(PORT).
#
#   make vr-accept   capture the baseline (do this before you start)
#   make vr          compare the current build against it
#
# Local only, never CI: font resolution differs on ubuntu, so macOS baselines
# would red-flag every run. `rake css:deadwood` is the CI-safe equivalent.
vr:
	NODE_PATH=$(NODE_PATH) node scripts/vr.mjs compare http://127.0.0.1:$(PORT)

vr-accept:
	NODE_PATH=$(NODE_PATH) node scripts/vr.mjs accept http://127.0.0.1:$(PORT)

images:
	./scripts/gen-images.sh

resume-pdf:
	uv run --with reportlab scripts/generate-resume-pdf.py assets/basant-bhattarai-resume.pdf

new-post:
	@test -n "$(SLUG)"  || { echo 'usage: make new-post SLUG=my-slug TITLE="My title"'; exit 1; }
	@test -n "$(TITLE)" || { echo 'usage: make new-post SLUG=my-slug TITLE="My title"'; exit 1; }
	@mkdir -p _drafts
	@test ! -f _drafts/$(SLUG).md || { echo "_drafts/$(SLUG).md already exists"; exit 1; }
	@sed -e 's|{{SLUG}}|$(SLUG)|g' \
	     -e 's|{{TITLE}}|$(TITLE)|g' \
	     -e 's|{{DATE}}|$(NOW)|g' \
	     _templates/post.md > _drafts/$(SLUG).md
	@echo "wrote _drafts/$(SLUG).md"
	@echo "when it is ready: mv _drafts/$(SLUG).md _posts/$(TODAY)-$(SLUG).md"

new-tutorial:
	@test -n "$(SLUG)"  || { echo 'usage: make new-tutorial SLUG=my-slug TITLE="My title"'; exit 1; }
	@test -n "$(TITLE)" || { echo 'usage: make new-tutorial SLUG=my-slug TITLE="My title"'; exit 1; }
	@mkdir -p _drafts
	@test ! -f _drafts/$(SLUG).md || { echo "_drafts/$(SLUG).md already exists"; exit 1; }
	@sed -e 's|{{SLUG}}|$(SLUG)|g' \
	     -e 's|{{TITLE}}|$(TITLE)|g' \
	     -e 's|{{DATE}}|$(NOW)|g' \
	     _templates/tutorial.md > _drafts/$(SLUG).md
	@echo "wrote _drafts/$(SLUG).md"
	@echo "when it is ready: mv _drafts/$(SLUG).md _posts/$(TODAY)-$(SLUG).md"

new-work:
	@test -n "$(SLUG)"  || { echo 'usage: make new-work SLUG=my-slug TITLE="My title"'; exit 1; }
	@test -n "$(TITLE)" || { echo 'usage: make new-work SLUG=my-slug TITLE="My title"'; exit 1; }
	@test ! -f _work/$(SLUG).md || { echo "_work/$(SLUG).md already exists"; exit 1; }
	@sed -e 's|{{SLUG}}|$(SLUG)|g' \
	     -e 's|{{TITLE}}|$(TITLE)|g' \
	     -e 's|{{DATE}}|$(NOW)|g' \
	     _templates/work.md > _work/$(SLUG).md
	@echo "wrote _work/$(SLUG).md"

clean:
	rm -rf _site .jekyll-cache .jekyll-metadata
