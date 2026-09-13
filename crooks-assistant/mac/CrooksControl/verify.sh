#!/bin/sh
# What can be checked about CROOKS Control on a machine that is not a Mac — and, just as
# importantly, what cannot.
#
# This is the gate the appliance's own CI runs. It is deliberately explicit about the third
# check being weaker than the first two: `swiftc -parse` proves the SwiftUI files are valid
# Swift and nothing else. It does not type-check them, it does not resolve SwiftUI or AppKit,
# and it will happily pass a view that calls a method that does not exist. A green run of this
# script is NOT evidence that the Mac app builds. Only `swift build` on a Mac is that.
#
# So this script does not have two answers, it has four, and "green" is not one of them off a
# Mac. §26 is one rule: A CHECK THAT CANNOT MEASURE SOMETHING MUST NOT REPORT A PASS. Exiting 0
# while printing "the Mac app builds — NOT RUN" broke it, and broke it in the direction that
# matters, because 0 is the only thing CI reads.
#
#   0   complete, and everything passed. Only reachable on a Mac, where check 4 really runs.
#   1   something failed.
#   2   no Swift toolchain: nothing here was checked at all.
#   3   INCOMPLETE. What could run, ran and passed — but the Mac app was never compiled, so
#       this run says nothing about whether CROOKS Control builds, draws or launches.
#
#   ./verify.sh          run everything it can
#   SWIFT=/path/to/swift ./verify.sh    with a toolchain somewhere unusual

set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
SWIFT=${SWIFT:-$(command -v swift || echo /opt/swift/usr/bin/swift)}
SWIFTC=${SWIFTC:-$(dirname "$SWIFT")/swiftc}
FAILED=0
# Set when a check could not be attempted on this machine. It is kept apart from FAILED because
# "broken" and "unmeasured" are different answers and collapsing them loses the only one CI can
# act on.
INCOMPLETE=0

if [ ! -x "$SWIFT" ]; then
  echo "NOT RUN  no Swift toolchain at $SWIFT — nothing here was checked." >&2
  exit 2
fi

echo "== 1. The core builds (Foundation only, every decision the app makes)"
cd "$HERE"
if "$SWIFT" build --target CrooksControlCore; then
  echo "   ok"
else
  echo "   FAILED"; FAILED=1
fi

echo
echo "== 2. The core's tests"
if "$SWIFT" test; then
  echo "   ok"
else
  echo "   FAILED"; FAILED=1
fi

echo
echo "== 3. The Mac app's sources parse (SYNTAX ONLY — see the note at the top of this file)"
if [ "$(uname -s)" = "Darwin" ]; then
  echo "   skipped: this is a Mac, so check 4 below is the real one"
elif "$SWIFTC" -parse "$HERE"/Sources/CrooksControl/*.swift; then
  echo "   ok — the files are valid Swift. They are NOT known to compile."
else
  echo "   FAILED"; FAILED=1
fi

echo
echo "== 4. The Mac app builds"
if [ "$(uname -s)" = "Darwin" ]; then
  if "$SWIFT" build --target CrooksControl; then
    echo "   ok"
  else
    echo "   FAILED"; FAILED=1
  fi
else
  echo "   NOT RUN. This is $(uname -s), and SwiftUI and AppKit do not exist here."
  echo "   Nothing in this run says anything about whether the Mac app compiles, draws,"
  echo "   or launches. Run this script on the Mac to find out."
  INCOMPLETE=1
fi

echo
if [ "$FAILED" -ne 0 ]; then
  echo "Something failed above." >&2
  exit 1
fi
if [ "$INCOMPLETE" -ne 0 ]; then
  # NOT a pass. The core is sound and the app is unmeasured, and those have to be one word
  # apart for anything reading the exit code — which is everything that matters.
  echo "INCOMPLETE. The core builds and its tests pass. The Mac app was NOT compiled, so"
  echo "nothing here says whether CROOKS Control builds. Run this on the Mac for that."
  exit 3
fi
echo "Everything this machine can check, it checked, and it passed — the Mac app included."
exit 0
