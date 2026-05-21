#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
DEFAULT_KROKI_URL="http://localhost:18473"
KROKI_URL="${KROKI_HOST_URL:-${KROKI_URL:-$DEFAULT_KROKI_URL}}"
HEALTH_TIMEOUT="${KROKI_HEALTH_TIMEOUT:-60}"

# When KROKI_HOST_URL is set, the user has pointed us at a Kroki instance they
# manage themselves — never start or stop the bundled docker compose.
EXTERNAL_KROKI=0
if [ -n "${KROKI_HOST_URL:-}" ]; then
  EXTERNAL_KROKI=1
fi

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [args...]

Commands:
  render <type> <source-file> <output-svg>   Render a diagram to SVG
  start                                       Start the bundled Kroki containers
  stop                                        Stop the bundled Kroki containers
  status                                      Report whether Kroki is healthy

Types: mermaid | graphviz | excalidraw | tikz

Environment:
  KROKI_HOST_URL         Use an externally managed Kroki at this URL. When set,
                         start/stop are disabled and render fails fast if the
                         URL is not healthy.
  KROKI_URL              Legacy alias for KROKI_HOST_URL.
  KROKI_HEALTH_TIMEOUT   Seconds to wait for health after start (default: 60).

If neither variable is set, the script targets $DEFAULT_KROKI_URL and manages
the bundled docker-compose stack on explicit start/stop. render does not
auto-start the stack — invoke start first.
EOF
}

is_healthy() {
  curl -fsS --max-time 2 "$KROKI_URL/health" >/dev/null 2>&1
}

wait_for_healthy() {
  local elapsed=0
  while ! is_healthy; do
    if [ "$elapsed" -ge "$HEALTH_TIMEOUT" ]; then
      echo "Kroki did not become healthy within ${HEALTH_TIMEOUT}s at $KROKI_URL" >&2
      return 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
}

start_compose() {
  if [ "$EXTERNAL_KROKI" -eq 1 ]; then
    echo "KROKI_HOST_URL is set ($KROKI_URL) — refusing to start docker compose." >&2
    echo "Unset KROKI_HOST_URL to use the bundled stack." >&2
    return 1
  fi
  if is_healthy; then
    echo "Kroki already healthy at $KROKI_URL" >&2
    return 0
  fi
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker not found on PATH — install Docker Desktop or the docker engine first" >&2
    return 1
  fi
  echo "Starting Kroki via docker compose..." >&2
  docker compose -f "$COMPOSE_FILE" up -d >&2
  wait_for_healthy
}

stop_compose() {
  if [ "$EXTERNAL_KROKI" -eq 1 ]; then
    echo "KROKI_HOST_URL is set ($KROKI_URL) — refusing to stop external Kroki." >&2
    return 1
  fi
  docker compose -f "$COMPOSE_FILE" down
}

require_healthy() {
  if is_healthy; then
    return 0
  fi
  if [ "$EXTERNAL_KROKI" -eq 1 ]; then
    echo "Kroki at $KROKI_URL is not healthy. Start it yourself or unset KROKI_HOST_URL." >&2
  else
    echo "Kroki is not running at $KROKI_URL. Start it with:" >&2
    echo "  $SCRIPT_DIR/$(basename "$0") start" >&2
  fi
  return 1
}

cmd_render() {
  if [ "$#" -ne 3 ]; then
    usage >&2
    exit 2
  fi
  local type="$1"
  local src="$2"
  local out="$3"

  case "$type" in
    mermaid|graphviz|excalidraw|tikz) ;;
    *)
      echo "Unknown type: $type (expected mermaid|graphviz|excalidraw|tikz)" >&2
      exit 2
      ;;
  esac

  if [ ! -f "$src" ]; then
    echo "Source file not found: $src" >&2
    exit 2
  fi

  require_healthy

  mkdir -p "$(dirname "$out")"

  curl -fsS \
    -X POST \
    -H "Content-Type: text/plain" \
    --data-binary "@$src" \
    -o "$out" \
    "$KROKI_URL/$type/svg"

  echo "Rendered: $out" >&2
}

cmd="${1:-}"
[ "$#" -gt 0 ] && shift

case "$cmd" in
  render) cmd_render "$@" ;;
  start)  start_compose ;;
  stop)   stop_compose ;;
  status)
    if is_healthy; then
      echo "Kroki is healthy at $KROKI_URL"
    else
      echo "Kroki is not running at $KROKI_URL"
      exit 1
    fi
    ;;
  ""|-h|--help|help) usage ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage >&2
    exit 2
    ;;
esac
