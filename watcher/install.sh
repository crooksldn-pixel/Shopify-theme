#!/usr/bin/env bash
#
# Install, remove or inspect the CROOKS AI bridge watcher.
#
#   sudo ./install.sh install        preflight, copy this reviewed tree into the runtime
#                                   directory, verify it, install the unit, seed, enable, start
#   ./install.sh verify              prove runtime == this source == installed unit
#   ./install.sh stage               copy into the runtime directory only (no systemd, no root
#                                   needed with CROOKS_BRIDGE_RUNTIME_DIR set)
#   sudo ./install.sh install --no-start   everything except starting it
#   sudo ./install.sh uninstall      stop, disable, remove the unit  (state is kept)
#   sudo ./install.sh uninstall --purge    the same, and delete /var/lib/crooks-bridge
#   ./install.sh status              what it has processed and whether it is running
#   ./install.sh preflight           check the prerequisites and change nothing
#
# Touches nothing belonging to crooks-assistant.service. Installing or removing this watcher
# cannot start, stop or reconfigure the assistant.

set -euo pipefail

# This script is the installer for the tree it lives in. THIS tree is the source of truth —
# whatever you reviewed and checked out — and installing copies it into the canonical runtime
# directory. That direction matters: the unit executes a fixed path, and if that path were also
# the place people edit, "approve commit X" could silently install something else that happened
# to be sitting there.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_WATCHER="$HERE/bin/crooks-bridge-watcher"
SRC_UNIT="$HERE/systemd/crooks-bridge-watcher.service"
SRC_README="$HERE/README.md"

RUNTIME_DIR="${CROOKS_BRIDGE_RUNTIME_DIR:-/opt/crooks-bridge-watcher}"
WATCHER="$RUNTIME_DIR/bin/crooks-bridge-watcher"
UNIT_SRC="$RUNTIME_DIR/systemd/crooks-bridge-watcher.service"
MANIFEST="$RUNTIME_DIR/MANIFEST.sha256"

UNIT_DST="/etc/systemd/system/crooks-bridge-watcher.service"
SERVICE="crooks-bridge-watcher.service"
STATE_DIR="${CROOKS_BRIDGE_STATE_DIR:-/var/lib/crooks-bridge}"

# What runtime consists of. Tests are NOT runtime: they exist to be run against the source before
# you trust it, and shipping them into the executed path only widens what is on disk as root.
payload() {
    printf '%s\n' "bin/crooks-bridge-watcher 0755" \
                   "systemd/crooks-bridge-watcher.service 0644" \
                   "README.md 0644"
}

source_revision() {
    git -C "$HERE" rev-parse HEAD 2>/dev/null || printf 'unknown (not a git checkout)'
}

stage() {
    # Copy the source payload into the runtime directory, with explicit modes, and record what
    # was installed. Safe to run repeatedly: every file is replaced, and the manifest is rewritten
    # from what is actually on disk afterwards rather than from what we intended to put there.
    local rel mode
    mkdir -p "$RUNTIME_DIR/bin" "$RUNTIME_DIR/systemd"
    while read -r rel mode; do
        [ -f "$HERE/$rel" ] || { bad "missing from source: $rel"; return 1; }
        install -D -m "$mode" "$HERE/$rel" "$RUNTIME_DIR/$rel" || return 1
    done < <(payload)

    {
        printf '# CROOKS AI bridge watcher runtime manifest\n'
        printf '# installed-from: %s\n' "$HERE"
        printf '# source-revision: %s\n' "$(source_revision)"
        printf '# installed-at: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        while read -r rel mode; do
            printf '%s  %s  %s\n' "$(sha256sum "$RUNTIME_DIR/$rel" | cut -d" " -f1)" "$mode" "$rel"
        done < <(payload)
    } > "$MANIFEST"
    chmod 0644 "$MANIFEST"
    ok "staged $(payload | wc -l) file(s) into $RUNTIME_DIR"
    ok "manifest $MANIFEST"
}

verify() {
    # Three things must agree: the source you reviewed, the runtime that will execute, and the
    # unit systemd has loaded. Any drift between them is the failure mode this whole subcommand
    # exists for — "approve commit X" must never install something else.
    local rel mode problems=0 src_sum run_sum
    [ -f "$MANIFEST" ] || { bad "no manifest at $MANIFEST — runtime was not installed by this script"; return 1; }

    while read -r rel mode; do
        if [ ! -f "$RUNTIME_DIR/$rel" ]; then
            bad "missing from runtime: $rel"; problems=$((problems+1)); continue
        fi
        src_sum="$(sha256sum "$HERE/$rel" | cut -d' ' -f1)"
        run_sum="$(sha256sum "$RUNTIME_DIR/$rel" | cut -d' ' -f1)"
        if [ "$src_sum" = "$run_sum" ]; then
            ok "matches source: $rel"
        else
            bad "DIFFERS from source: $rel"
            printf '        source : %s\n        runtime: %s\n' "$src_sum" "$run_sum"
            problems=$((problems+1))
        fi
        local actual; actual="$(stat -c '%a' "$RUNTIME_DIR/$rel")"
        [ "$actual" = "${mode#0}" ] || [ "0$actual" = "$mode" ] || {
            bad "wrong mode on $rel: expected $mode, found 0$actual"; problems=$((problems+1)); }
    done < <(payload)

    if [ -f "$UNIT_DST" ]; then
        if cmp -s "$UNIT_DST" "$UNIT_SRC"; then ok "installed unit matches runtime"
        else bad "installed unit DIFFERS from runtime — run: sudo $0 install"; problems=$((problems+1)); fi
    else
        warn "no unit installed at $UNIT_DST yet"
    fi

    grep -q '^# source-revision: ' "$MANIFEST" && printf '        %s\n' "$(grep '^# source-revision: ' "$MANIFEST")"

    [ "$problems" -eq 0 ] && { printf '\nRuntime matches source.\n'; return 0; }
    printf '\n%s mismatch(es).\n' "$problems" >&2
    return 1
}

ok()   { printf '[  ok  ] %s\n' "$*"; }
bad()  { printf '[ FAIL ] %s\n' "$*" >&2; }
warn() { printf '[ warn ] %s\n' "$*"; }

preflight() {
    local problems=0

    [ -x "$SRC_WATCHER" ] && ok "source watcher $SRC_WATCHER" || { bad "source watcher missing or not executable: $SRC_WATCHER"; problems=$((problems+1)); }
    [ -f "$SRC_UNIT" ] && ok "source unit $SRC_UNIT" || { bad "source unit missing: $SRC_UNIT"; problems=$((problems+1)); }
    ok "runtime target $RUNTIME_DIR"
    ok "source revision $(source_revision)"

    if command -v claude >/dev/null 2>&1; then
        ok "claude CLI $(command -v claude)"
        local claude_help
        claude_help="$(claude --help 2>&1 || true)"
        case "$claude_help" in *"--model"*) ok "claude CLI supports --model" ;;
            *) bad "claude CLI does not expose --model; update Claude Code before installing"; problems=$((problems+1)) ;; esac
        case "$claude_help" in *"--effort"*) ok "claude CLI supports --effort" ;;
            *) bad "claude CLI does not expose --effort; update Claude Code before installing"; problems=$((problems+1)) ;; esac
    else
        bad "the claude CLI is not on PATH"; problems=$((problems+1))
    fi

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
    local builder="${CROOKS_BRIDGE_WORKDIR:-/opt/crooks-builder}"
    local production="${CROOKS_BRIDGE_PRODUCTION_DIR:-/opt/crooks-os/crooks-assistant}"
    if [ "$(readlink -f "$builder" 2>/dev/null)" = "$(readlink -f "$production" 2>/dev/null)" ]; then
        bad "the builder worktree and the production checkout are the same directory"
        problems=$((problems+1))
    elif [ -d "$builder" ]; then
        ok "builder worktree $builder"
        # Clean before each task. Not enforced destructively: it is reported, never reset.
        if [ -n "$(git -C "$builder" status --porcelain=v1 --untracked-files=all 2>/dev/null)" ]; then
            warn "$builder has uncommitted changes — the watcher will REFUSE to run until they are"
            warn "resolved. Nothing here will discard them; look at them and commit or remove them."
        else
            ok "builder worktree clean"
        fi
    else
        bad "builder worktree missing: $builder"
        printf '        create it once with:\n          git -C /opt/crooks-os worktree add -b %s %s <production HEAD>\n' \
            "${CROOKS_BRIDGE_BUILDER_BRANCH:-claude/bridge-builder}" "$builder"
        problems=$((problems+1))
    fi
    [ -d "$production" ] && ok "production checkout $production (never edited by the watcher)" || \
        warn "production checkout not found at $production"

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

    stage || exit 1
    verify >/dev/null || { bad "runtime does not match source after staging — refusing to continue"; exit 1; }
    ok "runtime verified against source"

    install -m 0644 "$UNIT_SRC" "$UNIT_DST"
    ok "installed $UNIT_DST (from runtime, which matches source)"
    systemctl daemon-reload
    ok "systemd reloaded"

    # Seed BEFORE enabling, so the first thing the watcher does is not to re-execute an inbox
    # that has already been dealt with. From here on only a CHANGE starts a run.
    mkdir -p "$STATE_DIR"; chmod 700 "$STATE_DIR"
    if "$SRC_WATCHER" seed; then ok "state seeded at the current inbox"
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
    if [ -x "$WATCHER" ]; then "$WATCHER" status; else "$SRC_WATCHER" status; fi
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
    stage)     stage ;;
    verify)    verify ;;
    *) printf 'usage: %s {install [--no-start]|uninstall [--purge]|status|preflight|stage|verify}\n' "$0" >&2; exit 2 ;;
esac
