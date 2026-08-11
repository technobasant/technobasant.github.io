# technobasant.github.io
#
#   make serve        local preview (drafts + future posts + livereload)
#   make build        production build, same flags as CI
#   make check        html-proofer, internal only
#   make verify       output assertions against _site
#   make lighthouse   production build, then a clean server for auditing
#   make images       regenerate portrait derivatives, icons and social cards
#   make new-post SLUG=my-slug TITLE="My title"
#   make clean

SHELL   := /usr/bin/env bash
BUNDLE  := bundle exec
PORT    ?= 4000
# `date` on macOS has no --iso-8601; this format matches the contract exactly.
NOW     := $(shell TZ=Asia/Kathmandu date '+%Y-%m-%d %H:%M:%S %z')
TODAY   := $(shell TZ=Asia/Kathmandu date '+%Y-%m-%d')

.PHONY: help serve build check check-external verify jsonld lighthouse images new-post new-work clean

help:
	@grep -E '^#   ' $(MAKEFILE_LIST) | sed 's/^#   //'

# --future is mandatory: _config.yml sets `future: false` with
# `timezone: Asia/Kathmandu` (+0545), so a post dated later today is silently
# dropped from a local build and you spend an hour wondering where it went.
serve:
	$(BUNDLE) jekyll serve --drafts --future --livereload --port $(PORT)

build:
	JEKYLL_ENV=production $(BUNDLE) jekyll build --strict_front_matter --trace

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

images:
	./scripts/gen-images.sh

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
