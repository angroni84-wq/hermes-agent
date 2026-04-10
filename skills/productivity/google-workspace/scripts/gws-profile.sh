#!/usr/bin/env bash
set -euo pipefail

if ! command -v gws >/dev/null 2>&1; then
  echo "ERROR: gws CLI not found in PATH. Install Google's Google Workspace CLI first." >&2
  exit 127
fi

profile="${1:-${HERMES_GWS_PROFILE:-personal}}"
if [ "$#" -gt 0 ]; then
  shift
fi

case "$profile" in
  personal|default)
    default_dir="$HOME/.config/gws"
    ;;
  work)
    default_dir="$HOME/.config/gws-work"
    ;;
  *)
    echo "ERROR: unknown gws profile '$profile'. Use 'personal' or 'work', or set GOOGLE_WORKSPACE_CLI_CONFIG_DIR explicitly." >&2
    exit 2
    ;;
esac

export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="${GOOGLE_WORKSPACE_CLI_CONFIG_DIR:-$default_dir}"
exec gws "$@"
