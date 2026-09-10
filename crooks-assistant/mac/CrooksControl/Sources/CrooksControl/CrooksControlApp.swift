import AppKit
import SwiftUI

// The app. A dot and a line in the menu bar, a panel under it, and one window for the output
// of anything that takes longer than a moment.
//
// It does not need extravagant visuals. It needs to remove Terminal from normal ownership.

@main
struct CrooksControlApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @StateObject private var centre = Centre()

    var body: some Scene {
        MenuBarExtra {
            RootView(centre: centre)
                .frame(width: 380)
        } label: {
            // The glance: "CROOKS — Online", and a dot in the colour of the state.
            HStack(spacing: 4) {
                Image(systemName: centre.state.symbol)
                Text(centre.short)
            }
            .foregroundStyle(centre.tint)
        }
        .menuBarExtraStyle(.window)

        Window("CROOKS Control", id: Windows.output) {
            OutputView(log: centre.log)
        }
        .defaultSize(width: 720, height: 460)
    }
}

enum Windows {
    static let output = "output"
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // A menu-bar app has no Dock icon and no window at launch. The bundle says so too
        // (LSUIElement in Info.plist); this is here for a build run straight from the binary.
        NSApp.setActivationPolicy(.accessory)
    }
}

/// Everything the panel draws, and the only place that asks for it. One poll every fifteen
/// seconds, which is what /health's own cache is built for; a manual refresh skips the cache.
@MainActor
final class Centre: ObservableObject {
    @Published var status: StatusDocument?
    @Published var actions: [ActionsDocument.Action] = []
    @Published var plan: UpdateDocument?
    @Published var applied: UpdateDocument?
    @Published var problem: String?
    @Published var busy: String?
    @Published var log = CommandLog()

    private var poller: Task<Void, Never>?

    var state: Overall { status?.state ?? .red }
    var tint: Color { state.colour }
    /// The menu bar is narrow. "CROOKS — Online" fits; a sentence does not.
    var short: String { status?.headline ?? "CROOKS — ?" }

    func begin() {
        guard poller == nil else { return }
        poller = Task { [weak self] in
            while !Task.isCancelled {
                await self?.refresh()
                try? await Task.sleep(nanoseconds: 15 * 1_000_000_000)
            }
        }
    }

    func refresh() async {
        do {
            let control = try Control.here()
            let document = try await control.status()
            status = document
            if actions.isEmpty {
                actions = try await control.actions().actions
            }
            problem = nil
        } catch {
            problem = error.localizedDescription
            status = nil
        }
    }

    func check() async {
        busy = "Checking for an update…"
        defer { busy = nil }
        do {
            plan = try await Control.here().plan()
            applied = nil
        } catch {
            problem = error.localizedDescription
        }
    }

    func update() async {
        busy = "Updating: fast-forward, tests, restart, verify…"
        defer { busy = nil }
        do {
            applied = try await Control.here().apply()
            await refresh()
        } catch {
            problem = error.localizedDescription
        }
    }

    func rollBack() async {
        busy = "Going back to the last known-good build…"
        defer { busy = nil }
        do {
            applied = try await Control.here().rollback()
            await refresh()
        } catch {
            problem = error.localizedDescription
        }
    }

    /// A button. The document said what it is and what to run; this only obeys it.
    func perform(_ action: ActionsDocument.Action, openOutput: () -> Void) {
        switch action.kind {
        case "open_url":
            if let url = action.url.flatMap(URL.init(string:)) { NSWorkspace.shared.open(url) }
        case "open_path":
            if let path = action.path { revealNewest(in: path) }
        case "control":
            switch action.id {
            case "check": Task { await check() }
            case "update": Task { await update() }
            case "rollback": Task { await rollBack() }
            default: log.start(action); openOutput()
            }
        default:
            log.start(action)
            openOutput()
        }
    }

    /// "Open latest report" is the newest file in the folder the document named, or the folder
    /// itself when there is nothing in it yet.
    private func revealNewest(in path: String) {
        let url = URL(fileURLWithPath: path, isDirectory: true)
        let manager = FileManager.default
        let contents = (try? manager.contentsOfDirectory(at: url, includingPropertiesForKeys: [.contentModificationDateKey])) ?? []
        let newest = contents
            .filter { $0.pathExtension == "md" || $0.pathExtension == "html" }
            .max { left, right in
                let leftDate = (try? left.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
                let rightDate = (try? right.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
                return leftDate < rightDate
            }
        if let newest {
            NSWorkspace.shared.open(newest)
        } else {
            NSWorkspace.shared.open(url)
        }
    }

    func chooseFolder() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.prompt = "Use this folder"
        panel.message = "The CROOKS OS project folder — the one holding scripts/control.py."
        if panel.runModal() == .OK, let url = panel.url {
            Checkout.remember(url)
            actions = []
            Task { await refresh() }
        }
    }
}
