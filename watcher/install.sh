#!/usr/bin/env bash
#
# Install, remove or inspect the CROOKS AI bridge watcher.
#
#   sudo ./install.sh install        preflight, install the unit, seed the state, enable, start
#   sudo ./install.sh install --no-start   everything except starting it
#   sudo ./install.sh uninstall      stop, disable, remove the unit  (state is kept)
#   sudo ./install.sh uninstall --purge    the same, and delete /var/lib/crooks-bridge
#   ./install.sh status              what it has processed and whether it is running
#   ./install.sh preflight           check the prerequisites and change nothing
#
# Touches nothing belonging to crooks-assistant.service. Installing or removing this watcher
# cannot start, stop or reconfigure the assistant.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHER="$HERE/bin/crooks-bridge-watcher"
UNIT_SRC="$HERE/systemd/crooks-bridge-watcher.service"
UNIT_DST="/etc/systemd/system/crooks-bridge-watcher.service"
SERVICE="crooks-bridge-watcher.service"
STATE_DIR="${CROOKS_BRIDGE_STATE_DIR:-/var/lib/crooks-bridge}"

ok()   { printf '[  ok  ] %s\n' "$*"; }
bad()  { printf '[ FAIL ] %s\n' "$*" >&2; }
warn() { printf '[ warn ] %s\n' "$*"; }

preflight() {
    local problems=0

    [ -x "$WATCHER" ] && ok "watcher script $WATCHER" || { bad "watcher script missing or not executable: $WATCHER"; problems=$((problems+1)); }
    [ -f "$UNIT_SRC" ] && ok "unit template $UNIT_SRC" || { bad "unit template missing: $UNIT_SRC"; problems=$((problems+1)); }

    if command -v claude >/dev/null 2>&1; then ok "claude CLI $(command -v claude)"
    else bad "the claude CLI is not on PATH"; problems=$((problems+1)); fi

    if command -v gh >/dev/null 2>&1; then
        # Never prints the token: only whether the login works.
        if gh auth status >/dev/null 2>&1; then ok "gh authenticated"
        else bad "gh is installed but not authenticated — run: gh auth login"; problems=$((problems+1)); fi
    else bad "the gh CLI is not on PATH"; problems=$((problems+1)); fi

    command -v flock >/dev/null 2>&1 && ok "flock" || { bad "flock is missing (util-linux)"; problems=$((problems+1)); }
    command -v systemctl >/dev/null 2>&1 && ok "systemd" || { bad "systemd is missing"; problems=$((problems+1)); }

    [ -d "${CROOKS_BRIDGE_WORKTREE:-/opt/crooks-ai-bridge}" ] \
        && ok "bridge worktree ${CROOKS_BRIDGE_WORKTREE:-/opt/crooks-ai-bridge}" \
        || { bad "bridge worktree missing: ${CROOKS_BRIDGE_WORKTREE:-/opt/crooks-ai-bridge}"; problems=$((problems+1)); }
    [ -d "${CROOKS_BRIDGE_WORKDIR:-/opt/crooks-os/crooks-assistant}" ] \
        && ok "CROOKS checkout ${CROOKS_BRIDGE_WORKDIR:-/opt/crooks-os/crooks-assistant}" \
        || { bad "CROOKS checkout missing: ${CROOKS_BRIDGE_WORKDIR:-/opt/crooks-os/crooks-assistant}"; problems=$((problems+1)); }

    # The Claude Max login must be writable — the CLI rewrites it when the token refreshes.
    local creds="${HOME:-/root}/.claude/.credentials.json"
    if [ -f "$creds" ]; then
        [ -w "$creds" ] && ok "claude login present and writable" \
            || { bad "$creds is not writable — the token refresh would fail"; problems=$((problems+1)); }
    else
        warn "no $creds — run \`claude\` once and log in before starting the watcher"
    fi

    if [ "$problems" -eq 0 ]; then printf '\nPreflight clean.\n'; return 0; fi
    printf '\n%s problem(s). Fix them before installing.\n' "$problems" >&2
    return 1
}

require_root() {
    [ "$(id -u)" -eq 0 ] || { bad "this needs root: re-run with sudo"; exit 1; }
}

do_install() {
    require_root
    preflight || exit 1

    install -m 0644 "$UNIT_SRC" "$UNIT_DST"
    ok "installed $UNIT_DST"
    systemctl daemon-reload
    ok "systemd reloaded"

    # Seed BEFORE enabling, so the first thing the watcher does is not to re-execute an inbox
    # that has already been dealt with. From here on only a CHANGE starts a run.
    mkdir -p "$STATE_DIR"; chmod 700 "$STATE_DIR"
    if "$WATCHER" seed; then ok "state seeded at the current inbox"
    else bad "could not seed the state — GitHub unreachable?"; exit 1; fi

    systemctl enable "$SERVICE" >/dev/null 2>&1
    ok "enabled at boot"

    if [ "${1:-}" = "--no-start" ]; then
        warn "not started (--no-start). Start it with: systemctl start $SERVICE"
        return 0
    fi
    systemctl start "$SERVICE"
    ok "started"
    printf '\nFollow it with:  journalctl -u %s -f\n' "$SERVICE"
}

do_uninstall() {
    require_root
    systemctl stop "$SERVICE" 2>/dev/null && ok "stopped" || warn "was not running"
    systemctl disable "$SERVICE" >/dev/null 2>&1 && ok "disabled" || warn "was not enabled"
    [ -f "$UNIT_DST" ] && { rm -f "$UNIT_DST"; ok "removed $UNIT_DST"; } || warn "no unit file to remove"
    systemctl daemon-reload
    ok "systemd reloaded"

    if [ "${1:-}" = "--purge" ]; then
        rm -rf "$STATE_DIR"; ok "purged $STATE_DIR"
    else
        warn "state kept at $STATE_DIR (use --purge to delete it)"
    fi
    printf '\ncrooks-assistant.service was not touched.\n'
}

do_status() {
    "$WATCHER" status
    if command -v systemctl >/dev/null 2>&1 && [ -f "$UNIT_DST" ]; then
        printf '\n--- systemctl ---\n'
        systemctl status "$SERVICE" --no-pager --lines=0 2>&1 | head -6 || true
        printf '\n--- last journal lines ---\n'
        journalctl -u "$SERVICE" -n 10 --no-pager 2>/dev/null || true
    fi
}

case "${1:-status}" in
    install)   shift; do_install "${1:-}" ;;
    uninstall) shift; do_uninstall "${1:-}" ;;
    status)    do_status ;;
    preflight) preflight ;;
    *) printf 'usage: %s {install [--no-start]|uninstall [--purge]|status|preflight}\n' "$0" >&2; exit 2 ;;
esac
