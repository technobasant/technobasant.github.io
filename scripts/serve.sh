#!/usr/bin/env bash
# Local preview. Passes --drafts and --future by default:
# _config.yml sets `future: false` with `timezone: Asia/Kathmandu` (+0545), so a
# post dated later today is dropped from the build with no warning whatsoever.
# Anything you add on the command line is appended and wins.
#
# Usage: ./scripts/serve.sh [extra jekyll flags]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Native gem builds (ffi, eventmachine, sass-embedded) need the macOS SDK headers.
if command -v xcrun >/dev/null 2>&1; then
  SDKROOT="$(xcrun --show-sdk-path)"
  export SDKROOT
  export CPLUS_INCLUDE_PATH="${SDKROOT}/usr/include/c++/v1${CPLUS_INCLUDE_PATH:+:$CPLUS_INCLUDE_PATH}"
  export CPATH="${SDKROOT}/usr/include/c++/v1${CPATH:+:$CPATH}"
fi

bundle install
exec bundle exec jekyll serve --drafts --future --livereload "$@"
