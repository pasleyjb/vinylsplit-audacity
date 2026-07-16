#!/usr/bin/env bash
# Reset Audacity mod-script-pipe and launch VinylSplit.
set -euo pipefail

echo "==> Quitting Audacity"
pkill audacity 2>/dev/null || true
sleep 1
if pgrep -a audacity >/dev/null 2>&1; then
    echo "Audacity still running; trying again..."
    pkill -9 audacity 2>/dev/null || true
    sleep 1
fi
pgrep -a audacity || echo "Audacity is not running"

echo "==> Clearing stale pipes"
rm -f /tmp/audacity_script_pipe.to.* /tmp/audacity_script_pipe.from.*
if ls /tmp/audacity_script_pipe.* >/dev/null 2>&1; then
    echo "Warning: some pipe files remain:"
    ls -l /tmp/audacity_script_pipe.* || true
else
    echo "Pipes cleared (good)"
fi

echo "==> Starting Audacity"
audacity >/dev/null 2>&1 &
sleep 3

echo "==> Checking pipes"
if ls -l /tmp/audacity_script_pipe.* 2>/dev/null; then
    echo "Pipes look good."
else
    echo "ERROR: No pipes found."
    echo "In Audacity: Edit -> Preferences -> Modules"
    echo "Set mod-script-pipe to Enabled, OK, then re-run this script."
    exit 1
fi

echo "==> Starting VinylSplit"
if command -v vinylsplit >/dev/null 2>&1; then
    exec vinylsplit
elif [[ -x "$HOME/Development/vinylsplit-audacity/dist/vinylsplit/vinylsplit" ]]; then
    exec "$HOME/Development/vinylsplit-audacity/dist/vinylsplit/vinylsplit"
else
    echo "vinylsplit not found on PATH."
    exit 1
fi
