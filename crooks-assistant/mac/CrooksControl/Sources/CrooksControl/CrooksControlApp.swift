import AppKit
import SwiftUI
import CrooksControlCore

// The app. A window that IS the control centre, and a line in the menu bar for the glance.
//
// It does not need extravagant visuals. It needs to remove Terminal from normal ownership:
// turn the Mac on, and this is open, and everything that has to be done to CROOKS OS is a
// button on it.

@main
struct CrooksControlApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @StateObject private var centre = Centre()

    var body: some Scene {
        Window("CROOKS Control", id: Windows.control) {
            ControlCentreView(centre: centre)
        }
        // 420 WIDE, AND AS TALL AS ITS CONTENT. The rejected build opened at 720x760 for a panel
        // whose healthy state has four things on it, and the black left over read as a bug. This
        // is sized to the fullest state it can be in (about 400pt) and shrinks below that when
        // there is less to say.
        .defaultSize(width: 420, height: 400)
        .windowResizability(.contentSize)

        Window("CROOKS Output", id: Windows.output) {
            OutputView(log: centre.log)
        }
        .defaultSize(width: 760, height: 480)

        // The glance, for when the window is behind something. One word and a dot; everything
        // else is a click away in the window, where there is room to read it.
        MenuBarExtra {
            GlanceView(centre: centre)
        } label: {
            HStack(spacing: 4) {
                Image(systemName: symbol(centre.dashboard.lifecycle))
                Text(centre.dashboard.lifecycle.word.capitalized)
            }
        }
        .menuBarExtraStyle(.window)
    }

    private func symbol(_ phase: Lifecycle) -> String {
        switch phase {
        case .online: return "checkmark.circle.fill"
        case .offline: return "moon.circle.fill"
        case .starting, .stopping: return "arrow.triangle.2.circlepath.circle.fill"
        case .error: return "exclamationmark.octagon.fill"
        case .unknown: return "questionmark.circle"
        }
    }
}

enum Windows {
    static let control = "control"
    static let output = "output"
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    /// Closing the window is not quitting. The whole product promise is that CROOKS Control is
    /// simply THERE — closing the window and finding the app gone would make the owner reopen
    /// it from the Dock every time, which is one more thing to know.
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }
}

// MARK: - The control centre

struct ControlCentreView: View {
    @ObservedObject var centre: Centre
    @Environment(\.openWindow) private var openWindow
    @State private var showingDeveloper = false
    @State private var showingDetails = false

    /// One second, and it does nothing but let the core's own patience expire. Without it a
    /// START that never comes back would sit on "Starting…" until the next poll, or forever if
    /// the script had stopped answering entirely.
    private let clock = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    /// ONE SCREEN, composed in the core from the state. Everything the dashboard knows that is
    /// not on it is still reachable — System Details, and Developer Mode behind that — and none
    /// of it is drawn until it is asked for.
    private var screen: Screen {
        Presentation.screen(centre.dashboard, status: centre.status,
                            finished: centre.finishedTest, now: Date())
    }

    var body: some View {
        ScreenView(screen: screen) { action in
            switch action.id {
            case "details":
                showingDetails = true
            default:
                // The operation layer is untouched: the id came OUT of the actions document, so
                // it goes back into the same `perform` the old panel used. This view runs no
                // command of its own and knows what none of them do.
                if let button = centre.dashboard.groups.flatMap(\.buttons).first(where: { $0.id == action.id }) {
                    centre.perform(button) { openWindow(id: Windows.output) }
                }
            }
        }
        .task { centre.begin() }
        .onReceive(clock) { _ in centre.tick() }
        .sheet(isPresented: $showingDetails) {
            DetailsView(centre: centre, showingDeveloper: $showingDeveloper) { showingDetails = false }
        }
        .sheet(isPresented: $showingDeveloper) {
            if let panel = centre.dashboard.developer {
                DeveloperView(panel: panel) { showingDeveloper = false }
            }
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - The glance

struct GlanceView: View {
    @ObservedObject var centre: Centre
    @Environment(\.openWindow) private var openWindow

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 10) {
                Circle().fill(centre.accent).frame(width: 10, height: 10)
                Text(centre.dashboard.headline)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Ink.primary)
            }
            Text(centre.dashboard.explanation)
                .font(.system(size: 11.5)).foregroundStyle(Ink.secondary)
                .fixedSize(horizontal: false, vertical: true)
            HStack(spacing: 6) {
                Pip(health: centre.dashboard.pad.health)
                Text("CROOKS Pad — " + centre.dashboard.pad.word.lowercased())
                    .font(.system(size: 11)).foregroundStyle(Ink.tertiary)
            }
            Divider().overlay(Glass.lineSubtle)
            Button("Open CROOKS Control") { openWindow(id: Windows.control) }
                .keyboardShortcut(.defaultAction)
        }
        .padding(14)
        .frame(width: 300)
        .background(Ground.one)
    }
}
