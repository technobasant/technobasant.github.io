#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SDKROOT="$(xcrun --show-sdk-path)"
export SDKROOT
export CPLUS_INCLUDE_PATH="${SDKROOT}/usr/include/c++/v1${CPLUS_INCLUDE_PATH:+:$CPLUS_INCLUDE_PATH}"
export CPATH="${SDKROOT}/usr/include/c++/v1${CPATH:+:$CPATH}"
bundle install
exec bundle exec jekyll serve --livereload "$@"
