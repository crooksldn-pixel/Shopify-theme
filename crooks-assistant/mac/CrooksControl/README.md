# CROOKS Control

The menu bar says `CROOKS — Online`, in one of four colours, and everything under it is a
button instead of a line you type.

    GREEN   live and healthy
    BLUE    a test session is recording
    AMBER   live but read-only, or something non-essential is down, or the tablet has no route
    RED     nothing is answering, or hearing / Claude / Shopify is down

It shows: online, build, assistant, voice, the voice it speaks with, Claude, Shopify, Gmail,
the order cache, the tablet's address, whether changes could run, the test session, the branch
and build, and the last known-good build. It has the twelve buttons the brief asks for, plus
Roll back, which the update needs when a new build does not come up.

## Build it on the Mac

Three lines, in the project folder. It needs macOS 13 or later and the Xcode command line
tools (`xcode-select --install`, once).

    cd crooks-assistant
    make commands                    # put crooks-control on the PATH with the other commands
    make control-app                 # build the app and move it to /Applications

`make control-app` runs `mac/CrooksControl/build.sh --install`. To have it open at login as
well: `sh mac/CrooksControl/build.sh --login`. Then:

    open "/Applications/CROOKS Control.app"

The first run looks for the project in the usual places (`~/crooks-assistant`,
`~/Shopify-theme/crooks-assistant`, `~/Documents`, `~/Developer`, `~/code`). If it is
somewhere else, click **Project folder…** and choose the folder holding `scripts/control.py`.

Nothing about the backend changes: the assistant and whisper-server still start at login
through the launchd agents `make install` wrote, and this app only asks them to restart.

## What it is, and what it is not

The app is a renderer. Every colour, every row, every refusal and every command comes from
one place:

    crooks-control status      the colour, every row, both build ids   (no network)
    crooks-control plan        what an update would do: current vs candidate SHA
    crooks-control apply --yes the update itself
    crooks-control rollback --yes  back to the last known-good build, where that is safe
    crooks-control mark-good   record the running build as the one to come back to
    crooks-control actions     the buttons, and the command behind each
    crooks-control contract    what every field of every document above means

Try any of them in Terminal; the app sees exactly what you see. The app runs no command of
its own — no version control, no service manager, no test runner of its own idea — which is
why the logic can be tested on a machine with no Xcode on it (`tests/test_control.py`).

## The update, click by click

1. **Check for update** fetches the approved branch and shows `current → candidate`, how many
   commits, how many files, and whether dependencies changed. Nothing has moved.
2. **Update** appears only when it would be a fast-forward and the tree is clean. It
   fast-forwards, installs dependencies if they changed, runs the offline suite, restarts the
   launchd agents, reads `/health` back, checks the tablet's address, and records the build as
   known good.
3. If the suite fails or the backend does not come back, nothing is marked and **Roll back**
   is offered — to the last build that was recorded good. A rollback leaves the checkout on a
   detached HEAD deliberately: nothing is moved and nothing is lost. `git checkout <branch>`
   comes forward again.
4. A dirty tree stops all of it, and says which files. There is no force anywhere in this app
   or in the script under it.

## Files

    Package.swift                     the Swift package (macOS 13, one executable)
    Info.plist                        the bundle: LSUIElement, so no Dock icon
    build.sh                          build, assemble the .app, install, login item
    Sources/CrooksControl/
      Documents.swift                 the JSON, as types. Every field is in `crooks-control contract`
      Control.swift                   where the checkout is, and how the script is run
      CrooksControlApp.swift          the menu bar item and the poll
      Views.swift                     the rows, the buttons, the update, the output window
