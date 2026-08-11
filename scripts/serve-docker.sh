#!/usr/bin/env bash
# Preview technobasant.github.io without local Ruby native gems.
# Usage: ./scripts/serve-docker.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NAME="${JEKYLL_CONTAINER:-technobasant-jekyll}"
PORT="${PORT:-4000}"

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  docker rm -f "$NAME" >/dev/null
fi

echo "Starting Jekyll on http://127.0.0.1:${PORT} …"
docker run --rm -d --name "$NAME" -p "${PORT}:4000" \
  -v "$ROOT":/srv/jekyll \
  -w /srv/jekyll \
  -e JEKYLL_ENV=development \
  jekyll/jekyll:4.2.2 \
  bash -lc 'bundle install && jekyll serve --host 0.0.0.0 --port 4000 --livereload --force_polling'

echo "Logs: docker logs -f $NAME"
echo "Stop:  docker rm -f $NAME"
