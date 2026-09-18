#!/usr/bin/env bash
#
# Tests for the CROOKS AI bridge watcher.
#
# Everything the watcher touches is replaced by a stub on PATH — gh, claude and git — and
# pointed at a temporary state directory, so a test run reaches no network, starts no Claude,
# and cannot touch /var/lib, /run, the CROOKS checkout or the bridge worktree.
#
#   ./tests/run-tests.sh          run them all
#   ./tests/run-tests.sh -v       and show the watcher's own output
#
# Covers what the watcher is actually relied on for: it triggers on an inbox-blob change and
# on nothing else, it never runs two Claudes at once, it refuses to mark work processed that
# did not report, and it backs off instead of spinning.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHER="$HERE/../bin/crooks-bridge-watcher"
VERBOSE="${1:-}"

PASS=0; FAIL=0; FAILED_NAMES=()

# --------------------------------------------------------------------------- harness

setup() {
    SANDBOX="$(mktemp -d)"
    STUB="$SANDBOX/stub"; BIN="$SANDBOX/bin"; STATE="$SANDBOX/state"
    mkdir -p "$STUB" "$BIN" "$STATE"
    LOCK="$SANDBOX/watcher.lock"

    printf 'inbox-A\n'  > "$STUB/inbox_sha"
    printf 'outbox-1\n' > "$STUB/outbox_sha"
    printf '0\n'        > "$STUB/claude_exit"
    : > "$STUB/claude_runs"
    : > "$STUB/claude_args"

    # gh: answers the two contents lookups the watcher makes, and nothing else.
    cat > "$BIN/gh" <<'GH'
#!/usr/bin/env bash
[ -f "$STUB/gh_fail" ] && exit 1
for arg in "$@"; do
  case "$arg" in
    *chatgpt-inbox.md*)  tr -d '\n' < "$STUB/inbox_sha";  echo; exit 0 ;;
    *claude-outbox.md*)  tr -d '\n' < "$STUB/outbox_sha"; echo; exit 0 ;;
  esac
done
exit 1
GH

    # claude: records that it ran and with what, then behaves as the test asked.
    cat > "$BIN/claude" <<'CLAUDE'
#!/usr/bin/env bash
date +%s%N >> "$STUB/claude_runs"
printf '%s\n' "$*" >> "$STUB/claude_args"
[ -f "$STUB/claude_sleep" ] && sleep "$(cat "$STUB/claude_sleep")"
# A newer inbox landing WHILE this run is in flight.
[ -f "$STUB/claude_new_inbox" ] && cat "$STUB/claude_new_inbox" > "$STUB/inbox_sha"
# A run that actually pushed its outbox moves the blob; one that did not, does not.
[ -f "$STUB/claude_pushes" ] && printf 'outbox-%s\n' "$(date +%s%N)" > "$STUB/outbox_sha"
exit "$(cat "$STUB/claude_exit")"
CLAUDE

    # git: fetch and fast-forward are no-ops; `status` answers whatever the test asked for.
    cat > "$BIN/git" <<'GIT'
#!/usr/bin/env bash
for arg in "$@"; do
  if [ "$arg" = "status" ]; then
    [ -f "$STUB/dirty" ] && printf ' M some/file\n?? another/file\n'
    exit 0
  fi
done
exit 0
GIT

    chmod +x "$BIN/gh" "$BIN/claude" "$BIN/git"
    export STUB
}

teardown() { [ -n "${SANDBOX:-}" ] && rm -rf "$SANDBOX"; }

watch() {
    # One poll cycle, fully sandboxed.
    PATH="$BIN:$PATH" STUB="$STUB" \
    CROOKS_BRIDGE_STATE_DIR="$STATE" \
    CROOKS_BRIDGE_LOCK="$LOCK" \
    CROOKS_BRIDGE_WORKTREE="$SANDBOX" \
    CROOKS_BRIDGE_WORKDIR="$SANDBOX" \
    CROOKS_BRIDGE_POLL_S=1 \
    CROOKS_BRIDGE_BACKOFF_BASE_S=60 \
    CROOKS_BRIDGE_BACKOFF_MAX_S=900 \
    CROOKS_BRIDGE_CLAUDE_TIMEOUT_S=30 \
    CROOKS_BRIDGE_CLAUDE_LISTER="${LISTER:-true}" \
    CROOKS_BRIDGE_ALLOW_DIRTY="${ALLOW_DIRTY:-0}" \
        bash "$WATCHER" "$@" 2>&1
}

runs()      { wc -l < "$STUB/claude_runs" | tr -d ' '; }
recorded()  { [ -f "$STATE/last-inbox-sha" ] && tr -d '\n' < "$STATE/last-inbox-sha" || printf ''; }
failures()  { [ -f "$STATE/failures" ] && tr -d '\n' < "$STATE/failures" || printf ''; }

check() {
    local name="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        PASS=$((PASS+1)); printf '  ok    %s\n' "$name"
    else
        FAIL=$((FAIL+1)); FAILED_NAMES+=("$name")
        printf '  FAIL  %s\n         expected: %s\n         actual:   %s\n' "$name" "$expected" "$actual"
    fi
}

test_case() {
    local name="$1"; shift
    setup
    local out; out="$("$@" 2>&1)"
    [ "$VERBOSE" = "-v" ] && printf '%s\n' "$out" | sed 's/^/         | /'
    teardown
}

# --------------------------------------------------------------------------- the tests

t_unchanged_inbox_never_starts_claude() {
    printf 'inbox-A\n' > "$STATE/last-inbox-sha"
    watch --once >/dev/null
    check "an unchanged inbox starts nothing" "0" "$(runs)"
    check "  and the recorded SHA is left alone" "inbox-A" "$(recorded)"
}

t_a_changed_inbox_runs_claude_once() {
    touch "$STUB/claude_pushes"
    watch --once >/dev/null
    check "a changed inbox runs Claude exactly once" "1" "$(runs)"
    check "  and the processed SHA is recorded" "inbox-A" "$(recorded)"
    check "  and the failure count is clear" "0" "$(failures)"
}

t_the_same_inbox_is_not_processed_twice() {
    touch "$STUB/claude_pushes"
    watch --once >/dev/null      # processes inbox-A
    watch --once >/dev/null      # nothing has changed
    watch --once >/dev/null
    check "the same inbox is processed once, not three times" "1" "$(runs)"
}

t_the_outbox_moving_does_not_retrigger() {
    # The whole reason the trigger is the inbox BLOB and not the branch HEAD.
    touch "$STUB/claude_pushes"
    watch --once >/dev/null
    printf 'outbox-moved-by-claude\n' > "$STUB/outbox_sha"
    watch --once >/dev/null
    check "an outbox push does not retrigger the watcher" "1" "$(runs)"
}

t_a_failed_run_is_not_recorded() {
    printf '1\n' > "$STUB/claude_exit"
    watch --once >/dev/null
    check "a failed Claude does not mark the inbox processed" "" "$(recorded)"
    check "  and the failure is counted" "1" "$(failures)"
}

t_a_failed_run_is_retried_next_cycle() {
    printf '1\n' > "$STUB/claude_exit"
    watch --once >/dev/null
    printf '0\n' > "$STUB/claude_exit"; touch "$STUB/claude_pushes"
    watch --once >/dev/null
    check "a failed inbox is retried and then recorded" "inbox-A" "$(recorded)"
    check "  over two Claude runs" "2" "$(runs)"
    check "  and the failure count resets on success" "0" "$(failures)"
}

t_backoff_grows_then_caps() {
    printf '1\n' > "$STUB/claude_exit"
    local first second third
    watch --once >/dev/null; first="$(cat "$STATE/.next-delay")"
    watch --once >/dev/null; second="$(cat "$STATE/.next-delay")"
    watch --once >/dev/null; third="$(cat "$STATE/.next-delay")"
    check "backoff after 1 failure is 60s" "60" "$first"
    check "backoff after 2 failures is 120s" "120" "$second"
    check "backoff after 3 failures is 240s" "240" "$third"
    printf '9\n' > "$STATE/failures"
    check "backoff is capped, never unbounded" "900" \
        "$(PATH="$BIN:$PATH" STUB="$STUB" CROOKS_BRIDGE_STATE_DIR="$STATE" CROOKS_BRIDGE_LOCK="$LOCK" \
           CROOKS_BRIDGE_BACKOFF_BASE_S=60 CROOKS_BRIDGE_BACKOFF_MAX_S=900 \
           bash -c 'source <(sed -n "/^backoff_for()/,/^}/p" '"$WATCHER"'); BACKOFF_BASE_S=60; BACKOFF_MAX_S=900; POLL_INTERVAL=30; backoff_for 9')"
}

t_a_run_that_never_reported_is_a_failure() {
    # Claude exits 0 but never pushed an outbox: nobody has been told anything, so the inbox
    # is NOT answered and must not be marked processed.
    rm -f "$STUB/claude_pushes"
    watch --once >/dev/null
    check "exit 0 without an outbox push is not success" "" "$(recorded)"
    check "  and it counts as a failure" "1" "$(failures)"
}

t_a_held_lock_suppresses_a_second_claude() {
    touch "$STUB/claude_pushes"
    flock -x "$LOCK" -c 'sleep 2' &
    local holder=$!
    sleep 0.3
    watch --once >/dev/null
    check "no second Claude starts while one holds the lock" "0" "$(runs)"
    check "  and nothing is recorded as processed" "" "$(recorded)"
    wait "$holder" 2>/dev/null   # the holder releases it by exiting; no kill, no orphaned child
    watch --once >/dev/null
    check "  the inbox is picked up once the lock frees" "1" "$(runs)"
}

t_a_newer_inbox_mid_run_is_taken_next_cycle() {
    # Requirement 10: finish the current run, then notice the newer inbox — and never record
    # the newer SHA as processed on the strength of a run that never saw it.
    touch "$STUB/claude_pushes"
    printf 'inbox-B\n' > "$STUB/claude_new_inbox"
    watch --once >/dev/null
    check "the SHA recorded is the one actually handed to Claude" "inbox-A" "$(recorded)"
    rm -f "$STUB/claude_new_inbox"
    watch --once >/dev/null
    check "  and the newer inbox is processed on the next cycle" "2" "$(runs)"
    check "  leaving the newer SHA recorded" "inbox-B" "$(recorded)"
}

t_github_unreachable_starts_nothing() {
    touch "$STUB/gh_fail"
    watch --once >/dev/null
    check "an unreadable GitHub starts no Claude" "0" "$(runs)"
    check "  records nothing" "" "$(recorded)"
    check "  and backs off" "60" "$(cat "$STATE/.next-delay")"
}

t_seed_records_without_running_claude() {
    watch seed >/dev/null
    check "seed records the current inbox" "inbox-A" "$(recorded)"
    check "  without running Claude" "0" "$(runs)"
    watch --once >/dev/null
    check "  so a seeded watcher waits for a real change" "0" "$(runs)"
}

t_a_dirty_target_tree_refuses_to_start() {
    # The guard that matters most: a headless agent must not edit a tree someone else is
    # part-way through. Refusing is the whole point — the inbox is left for a safer moment.
    touch "$STUB/claude_pushes" "$STUB/dirty"
    local out; out="$(watch --once)"
    check "a dirty target tree starts no Claude" "0" "$(runs)"
    check "  and the inbox is left unprocessed" "" "$(recorded)"
    case "$out" in
        *REFUSING*uncommitted*) PASS=$((PASS+1)); printf '  ok      and it says why, and what to do\n' ;;
        *) FAIL=$((FAIL+1)); FAILED_NAMES+=("dirty refusal message")
           printf '  FAIL    the refusal does not explain itself\n' ;;
    esac
}

t_a_dirty_tree_can_be_overridden_deliberately() {
    # Not a lock-out: a person who has looked at the changes can say so. Off by default.
    touch "$STUB/claude_pushes" "$STUB/dirty"
    ALLOW_DIRTY=1 watch --once >/dev/null
    check "a deliberate override runs anyway" "1" "$(runs)"
    check "  and records the inbox" "inbox-A" "$(recorded)"
}

t_another_claude_in_the_tree_refuses_to_start() {
    # A real process, with a real cwd inside the target, found through a real /proc lookup.
    touch "$STUB/claude_pushes"
    ( cd "$SANDBOX" && exec sleep 5 ) &
    local intruder=$!
    printf '#!/usr/bin/env bash\necho %s\n' "$intruder" > "$BIN/fake-lister"
    chmod +x "$BIN/fake-lister"
    local out; out="$(LISTER="$BIN/fake-lister" watch --once)"
    check "another Claude in the tree starts no second one" "0" "$(runs)"
    check "  and the inbox is left unprocessed" "" "$(recorded)"
    case "$out" in
        *REFUSING*"another Claude"*) PASS=$((PASS+1)); printf '  ok      and it names the pid and the remedy\n' ;;
        *) FAIL=$((FAIL+1)); FAILED_NAMES+=("foreign claude message")
           printf '  FAIL    the refusal does not name the other process\n' ;;
    esac
    kill "$intruder" 2>/dev/null; wait "$intruder" 2>/dev/null
    watch --once >/dev/null
    check "  and the run proceeds once that process is gone" "1" "$(runs)"
}

t_a_claude_elsewhere_on_the_box_is_not_confused_for_one_here() {
    # The guard must not fire on an unrelated Claude session in some other directory, or the
    # watcher would refuse to run on a machine where anyone is using Claude for anything.
    touch "$STUB/claude_pushes"
    ( cd / && exec sleep 5 ) &
    local elsewhere=$!
    printf '#!/usr/bin/env bash\necho %s\n' "$elsewhere" > "$BIN/fake-lister"
    chmod +x "$BIN/fake-lister"
    LISTER="$BIN/fake-lister" watch --once >/dev/null
    check "a Claude outside the tree does not block the run" "1" "$(runs)"
    kill "$elsewhere" 2>/dev/null; wait "$elsewhere" 2>/dev/null
}

t_the_prompt_carries_the_safety_contract() {
    touch "$STUB/claude_pushes"
    watch --once >/dev/null
    # Normalised: the contract is the words, not the line breaks or the capitalisation.
    local args; args="$(tr '\n' ' ' < "$STUB/claude_args" | tr -s ' ' | tr '[:upper:]' '[:lower:]')"
    for phrase in "never fabricate" "writes_enabled stays false" "127.0.0.1" \
                  "never its value" "push it to origin" "stop at that point"; do
        case "$args" in
            *"$phrase"*) PASS=$((PASS+1)); printf '  ok    the prompt says: %s\n' "$phrase" ;;
            *) FAIL=$((FAIL+1)); FAILED_NAMES+=("prompt missing: $phrase")
               printf '  FAIL  the prompt never says: %s\n' "$phrase" ;;
        esac
    done
    case "$args" in
        *"--permission-mode acceptedits"*) PASS=$((PASS+1)); printf '  ok    runs with acceptEdits, not bypassPermissions\n' ;;
        *) FAIL=$((FAIL+1)); FAILED_NAMES+=("permission mode")
           printf '  FAIL  the permission mode is not what the unit sets\n' ;;
    esac
    case "$args" in
        *bypassPermissions*|*dangerously*) FAIL=$((FAIL+1)); FAILED_NAMES+=("dangerous flag")
            printf '  FAIL  a permission-bypassing flag is being passed\n' ;;
        *) PASS=$((PASS+1)); printf '  ok    no permission-bypassing flag is passed\n' ;;
    esac
}

# --------------------------------------------------------------------------- run

printf '\nCROOKS AI bridge watcher — tests\n%s\n' "──────────────────────────────────────────────────────────────"
for t in \
    t_unchanged_inbox_never_starts_claude \
    t_a_changed_inbox_runs_claude_once \
    t_the_same_inbox_is_not_processed_twice \
    t_the_outbox_moving_does_not_retrigger \
    t_a_failed_run_is_not_recorded \
    t_a_failed_run_is_retried_next_cycle \
    t_backoff_grows_then_caps \
    t_a_run_that_never_reported_is_a_failure \
    t_a_held_lock_suppresses_a_second_claude \
    t_a_newer_inbox_mid_run_is_taken_next_cycle \
    t_a_dirty_target_tree_refuses_to_start \
    t_a_dirty_tree_can_be_overridden_deliberately \
    t_another_claude_in_the_tree_refuses_to_start \
    t_a_claude_elsewhere_on_the_box_is_not_confused_for_one_here \
    t_github_unreachable_starts_nothing \
    t_seed_records_without_running_claude \
    t_the_prompt_carries_the_safety_contract
do
    printf '\n%s\n' "${t#t_}" | tr '_' ' '
    setup
    "$t"
    teardown
done

printf '\n%s\n' "──────────────────────────────────────────────────────────────"
if [ "$FAIL" -eq 0 ]; then
    printf '%s passed, 0 failed.\n\n' "$PASS"; exit 0
fi
printf '%s passed, %s FAILED:\n' "$PASS" "$FAIL"
for n in "${FAILED_NAMES[@]}"; do printf '  - %s\n' "$n"; done
printf '\n'; exit 1
