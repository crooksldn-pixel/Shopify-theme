import AppKit
import SwiftUI
import CrooksControlCore

// SYSTEM DETAILS — the middle rung of the disclosure ladder.
//
//   the front page     one word, one line, one action
//   System Details     every service the script reported, and every control it offers
//   Developer Mode     the internals: raw rows, argv, the SHA, the port, the last failure
//
// The rejected build had this rung's contents ON the front page: seven integrations as an admin
// table, ten buttons visible at once. None of that is deleted — a capability the owner has today
// he still has — it is one click away instead of permanently in the way, which is the whole of
// the difference between a product and a control panel.

struct DetailsView: View {
    @ObservedObject var centre: Centre
    @Binding var showingDeveloper: Bool
    let close: () -> Void

    @Environment(\.openWindow) private var openWindow

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    services
                    controls
                    identity
                }
                .padding(20)
            }
            footer
        }
        .frame(width: 460, height: 560)
        .background(Ground.base.ignoresSafeArea())
    }

    private var header: some View {
        HStack {
            Text("SYSTEM DETAILS")
                .font(.system(size: 10.5, weight: .bold)).tracking(2)
                .foregroundStyle(Ink.tertiary)
            Spacer()
            Button("Done", action: close)
                .buttonStyle(.plain)
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(Ink.secondary)
        }
        .padding(.horizontal, 20).padding(.vertical, 15)
        .overlay(alignment: .bottom) { Rectangle().fill(Glass.lineSubtle).frame(height: 1) }
    }

    /// Compact service state — a list, not a table. Everything that is WELL is one dim line; the
    /// eye should land only on what is not.
    private var services: some View {
        VStack(alignment: .leading, spacing: 0) {
            sectionLabel("SERVICES")
            ForEach(centre.dashboard.services) { tile in
                HStack(spacing: 10) {
                    Circle().fill(colour(tile.health)).frame(width: 5, height: 5)
                    Text(tile.name)
                        .font(.system(size: 12.5))
                        .foregroundStyle(tile.health == .bad ? Ink.primary : Ink.secondary)
                    Spacer(minLength: 12)
                    Text(tile.value)
                        .font(.system(size: 11.5))
                        .foregroundStyle(tile.health == .bad ? Signal.bad : Ink.quaternary)
                        .lineLimit(1).truncationMode(.middle)
                }
                .padding(.vertical, 7)
                .overlay(alignment: .bottom) { Rectangle().fill(Glass.lineSubtle.opacity(0.5)).frame(height: 1) }
            }
        }
    }

    /// Every control the script offers, including the ones the front page did not need today.
    private var controls: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionLabel("CONTROLS")
            ForEach(centre.dashboard.groups) { group in
                FlowRow(spacing: 8) {
                    ForEach(group.buttons) { button in
                        ActionChip(button: button) { pressed in
                            centre.perform(pressed) { openWindow(id: Windows.output) }
                            close()
                        }
                    }
                }
            }
            // Invariant 12, still said in words — the front page has no room for it and it must
            // not therefore go unsaid.
            if !centre.dashboard.missingControls.isEmpty {
                VStack(alignment: .leading, spacing: 5) {
                    Text("NOT AVAILABLE")
                        .font(.system(size: 9.5, weight: .bold)).tracking(1.6)
                        .foregroundStyle(Signal.warn)
                    Text(centre.dashboard.missingControls.joined(separator: " · "))
                        .font(.system(size: 12)).foregroundStyle(Ink.secondary)
                    Text("CROOKS OS on this Mac does not offer "
                         + (centre.dashboard.missingControls.count == 1 ? "this control" : "these controls")
                         + ". Install CROOKS Control again from this CROOKS OS folder to get "
                         + (centre.dashboard.missingControls.count == 1 ? "it" : "them") + " back.")
                        .font(.system(size: 11)).foregroundStyle(Ink.quaternary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: Radius.control, style: .continuous)
                    .fill(Signal.warn.opacity(0.09)))
                .overlay(RoundedRectangle(cornerRadius: Radius.control, style: .continuous)
                    .strokeBorder(Signal.warn.opacity(0.30), lineWidth: 1))
            }
        }
    }

    private var identity: some View {
        VStack(alignment: .leading, spacing: 0) {
            sectionLabel("THIS BUILD")
            row("Running", centre.dashboard.identity.runningBuild)
            row("Checkout", centre.dashboard.identity.checkout)
            row("Known good", centre.dashboard.identity.lastKnownGood)
            row("Up", centre.dashboard.identity.uptime)
        }
    }

    private func row(_ name: String, _ value: String) -> some View {
        HStack(spacing: 12) {
            Text(name).font(.system(size: 12)).foregroundStyle(Ink.tertiary)
            Spacer(minLength: 12)
            Text(value.isEmpty ? "—" : value)
                .font(.system(size: 11.5, design: .monospaced))
                .foregroundStyle(Ink.secondary)
                .lineLimit(1).truncationMode(.middle)
        }
        .padding(.vertical, 7)
        .overlay(alignment: .bottom) { Rectangle().fill(Glass.lineSubtle.opacity(0.5)).frame(height: 1) }
    }

    private var footer: some View {
        HStack {
            Toggle("Developer Mode", isOn: $centre.developerMode)
                .toggleStyle(.switch).controlSize(.mini)
                .font(.system(size: 11)).foregroundStyle(Ink.tertiary)
            Spacer()
            if centre.developerMode {
                Button("Open Developer") {
                    close()
                    showingDeveloper = true
                }
                .buttonStyle(.plain)
                .font(.system(size: 11)).foregroundStyle(Ink.secondary)
            }
            // The three that used to sit permanently along the bottom of the front page. They
            // are still here and still one click away; what they are not is on screen while the
            // owner is trying to read one word.
            Button("Output") { close(); openWindow(id: Windows.output) }
                .buttonStyle(.plain).font(.system(size: 11)).foregroundStyle(Ink.tertiary)
            Button("Folder…") { centre.chooseFolder() }
                .buttonStyle(.plain).font(.system(size: 11)).foregroundStyle(Ink.tertiary)
            Button("Quit") { NSApp.terminate(nil) }
                .buttonStyle(.plain).font(.system(size: 11)).foregroundStyle(Ink.tertiary)
        }
        .padding(.horizontal, 20).padding(.vertical, 13)
        .overlay(alignment: .top) { Rectangle().fill(Glass.lineSubtle).frame(height: 1) }
    }

    private func colour(_ health: Health) -> Color {
        switch health {
        case .ok: return Ink.quaternary
        case .off: return Ink.quaternary.opacity(0.6)
        case .bad: return Signal.bad
        case .notReported: return Ink.quaternary.opacity(0.4)
        }
    }

    private func sectionLabel(_ text: String) -> some View {
        Text(text)
            .font(.system(size: 9.5, weight: .bold)).tracking(1.8)
            .foregroundStyle(Ink.quaternary)
            .padding(.bottom, 8)
    }
}
