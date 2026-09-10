// swift-tools-version:5.9
//
// CROOKS Control — the menu-bar app for the Mac that runs CROOKS OS.
//
// It renders the JSON that scripts/control.py prints and runs the commands that document
// names. It contains no idea of its own about how to update, restart or test this Mac: those
// live in the scripts, where they are tested. See mac/CrooksControl/README.md to build it.

import PackageDescription

let package = Package(
    name: "CrooksControl",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "CrooksControl",
            path: "Sources/CrooksControl"
        )
    ]
)
