import AppKit
import SwiftUI

// The panel. Rows at the top, buttons under them, and the update — which is the one thing
// here that needs two clicks: one to see what is coming, one to take it.

extension Overall {
    /// The four colours, drawn. The system's own, so they follow light and dark and the
    /// increase-contrast setting without a palette of ours.
    var colour: Color {
        switch self {
        case .green: return Color(nsColor: .systemGreen)
        case .blue: return Color(nsColor: .systemBlue)
        case .amber: return Color(nsColor: .systemOrange)
        case .red: return Color(nsColor: .systemRed)
        }
    }
}

struct RootView: View {
    @ObservedObject var centre: Centre
    @Environment(\.openWindow) private var openWindow
    @State private var asking: ActionsDocument.Action?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            header
            if let problem = centre.problem {
                Problem(text: problem, chooseFolder: centre.chooseFolder)
            }
            if let status = centre.status {
                Divider()
                StatusRows(rows: status.rows)
                Divider()
                UpdateSection(centre: centre, status: status)
                Divider()
                Buttons(centre: centre, ask: { asking = $0 }, openOutput: { openWindow(id: Windows.output) })
            }
            Divider()
            Footer(centre: centre)
        }
        .padding(12)
        .task { centre.begin() }
        .alert(asking?.label ?? "", isPresented: .init(get: { asking != nil }, set: { if !$0 { asking = nil } })) {
            Button("Cancel", role: .cancel) { asking = nil }
            Button(asking?.label ?? "Do it") {
                if let action = asking {
                    centre.perform(action) { openWindow(id: Windows.output) }
                }
                asking = nil
            }
        } message: {
            Text(asking?.confirmText ?? "")
        }
    }

    private var header: some View {
        HStack(spacing: 8) {
            Image(systemName: centre.state.symbol)
                .foregroundStyle(centre.tint)
                .font(.title3)
            VStack(alignment: .leading, spacing: 1) {
                Text(centre.short).font(.headline)
                Text(centre.status?.why ?? "").font(.caption).foregroundStyle(.secondary)
                    .lineLimit(3).fixedSize(horizontal: false, vertical: true)
            }
            Spacer()
            if centre.busy != nil {
                ProgressView().controlSize(.small)
            } else {
                Button {
                    Task { await centre.refresh() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.borderless)
                .help("Read it again now")
            }
        }
    }
}

struct StatusRows: View {
    let rows: [StatusDocument.Row]

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            ForEach(rows) { row in
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Circle()
                        .fill(colour(row.state))
                        .frame(width: 7, height: 7)
                    Text(row.label)
                        .font(.system(size: 11, weight: .medium))
                        .frame(width: 92, alignment: .leading)
                    Text(row.value)
                        .font(.system(size: 11))
                        .foregroundStyle(row.state == "bad" ? .primary : .secondary)
                        .lineLimit(2)
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer(minLength: 0)
                }
                .help(row.detail.isEmpty ? row.value : "\(row.value)\n\(row.detail)")
            }
        }
    }

    private func colour(_ state: String) -> Color {
        switch state {
        case "ok": return Color(nsColor: .systemGreen)
        case "bad": return Color(nsColor: .systemRed)
        default: return Color(nsColor: .tertiaryLabelColor)
        }
    }
}

/// Check, then click. The SHAs are shown before anything moves, because that is the moment
/// the owner decides.
struct UpdateSection: View {
    @ObservedObject var centre: Centre
    let status: StatusDocument

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            if let busy = centre.busy {
                Text(busy).font(.caption).foregroundStyle(.secondary)
            }
            if let applied = centre.applied {
                Outcome(document: applied)
            } else if let plan = centre.plan, let update = plan.update {
                Text(sentence(for: update, next: plan.next ?? ""))
                    .font(.system(size: 11))
                    .fixedSize(horizontal: false, vertical: true)
                if let stop = plan.stop ?? update.stop {
                    Text(stop.reason).font(.caption).foregroundStyle(Color(nsColor: .systemRed))
                        .fixedSize(horizontal: false, vertical: true)
                }
                if plan.click?.enabled == true, let localWork = plan.localWork, !localWork.stops {
                    Button("Update to \(update.candidate?.short ?? "the new build") now") {
                        Task { await centre.update() }
                    }
                    .disabled(centre.busy != nil)
                }
            }
            if status.rollback.available {
                HStack(spacing: 6) {
                    Button("Roll back to \(status.rollback.short)") { Task { await centre.rollBack() } }
                        .disabled(!status.rollback.safe || centre.busy != nil)
                    if !status.rollback.safe {
                        Text(status.rollback.reason)
                            .font(.caption).foregroundStyle(.secondary).lineLimit(2)
                    }
                }
            }
        }
    }

    private func sentence(for update: UpdateDocument.Update, next: String) -> String {
        let current = update.current?.short ?? "?"
        switch next {
        case "up_to_date":
            return "Up to date at \(current)."
        case "click_to_apply":
            let candidate = update.candidate?.short ?? "?"
            let deps = update.deps.isEmpty ? "" : " Dependencies changed (\(update.deps.joined(separator: ", ")))."
            return "\(current) → \(candidate): \(update.behind) commit(s), \(update.changedFiles) file(s)."
                + (update.fastForward ? "" : " NOT a fast-forward.") + deps
        default:
            return "Nothing was changed."
        }
    }
}

struct Outcome: View {
    let document: UpdateDocument

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(headline).font(.system(size: 11, weight: .medium))
            ForEach((document.update?.stages ?? []) + (document.stages ?? [])) { stage in
                Text("\(mark(stage.state))  \(stage.stage)  \(stage.detail)")
                    .font(.system(size: 10, design: .monospaced))
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if let stop = document.stop ?? document.update?.stop {
                Text(stop.reason).font(.caption).foregroundStyle(Color(nsColor: .systemRed))
                    .fixedSize(horizontal: false, vertical: true)
            }
            if document.next == "rollback", let rollback = document.rollback, rollback.safe {
                Text(rollback.reason).font(.caption)
            }
        }
    }

    private var headline: String {
        switch document.next ?? "" {
        case "done": return "Updated to \(document.markedGood?.short ?? "the new build") and marked good."
        case "up_to_date": return "Already up to date."
        case "rollback": return "It did not come up. Rolling back is safe."
        case "verify_by_hand": return "It moved, but the backend has not read back healthy yet."
        default: return document.ok ? "Done." : "Stopped, and nothing was changed."
        }
    }

    private func mark(_ state: String) -> String {
        switch state {
        case "ok": return "ok  "
        case "fail": return "FAIL"
        case "warn": return "warn"
        default: return "--  "
        }
    }
}

struct Buttons: View {
    @ObservedObject var centre: Centre
    let ask: (ActionsDocument.Action) -> Void
    let openOutput: () -> Void

    private let order = ["use", "update", "test", "look"]
    /// The three the update section draws itself, with the SHAs beside them.
    private let handledAbove = ["check", "update", "rollback"]

    private func actions(in group: String) -> [ActionsDocument.Action] {
        centre.actions.filter { $0.group == group && !handledAbove.contains($0.id) }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            ForEach(order, id: \.self) { group in
                HStack(spacing: 6) {
                    ForEach(actions(in: group)) { action in
                        Button(action.label) {
                            if action.confirm { ask(action) } else { centre.perform(action) { openOutput() } }
                        }
                        .help(action.why)
                    }
                }
            }
            HStack(spacing: 6) {
                Button("Check for update") { Task { await centre.check() } }
                    .disabled(centre.busy != nil)
                    .help("Fetches and shows both build ids. Changes nothing.")
            }
        }
        .controlSize(.small)
    }
}

struct Footer: View {
    @ObservedObject var centre: Centre

    var body: some View {
        HStack {
            if let build = centre.status?.build.current {
                Text("\(build.branch ?? "") \(build.short ?? "")")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Button("Project folder…") { centre.chooseFolder() }
                .buttonStyle(.borderless)
                .font(.caption)
            Button("Quit") { NSApp.terminate(nil) }
                .buttonStyle(.borderless)
                .font(.caption)
        }
    }
}

struct Problem: View {
    let text: String
    let chooseFolder: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(text).font(.system(size: 11)).fixedSize(horizontal: false, vertical: true)
            Button("Choose the project folder…", action: chooseFolder).controlSize(.small)
        }
        .padding(6)
        .background(Color(nsColor: .controlBackgroundColor))
    }
}

/// The window the longer commands print into: the suite, the UI run, a report.
struct OutputView: View {
    @ObservedObject var log: CommandLog

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(log.title.isEmpty ? "Output" : log.title).font(.headline)
                if log.running { ProgressView().controlSize(.small) }
                Spacer()
                if let finished = log.finished {
                    Text(finished == 0 ? "finished" : "finished with \(finished)")
                        .font(.caption)
                        .foregroundStyle(finished == 0 ? .secondary : Color(nsColor: .systemRed))
                }
                if log.running {
                    Button("Stop") { log.stop() }
                }
            }
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        ForEach(Array(log.lines.enumerated()), id: \.offset) { pair in
                            Text(pair.element)
                                .font(.system(size: 11, design: .monospaced))
                                .textSelection(.enabled)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .id(pair.offset)
                        }
                    }
                    .padding(6)
                }
                .onChange(of: log.lines.count) { count in
                    proxy.scrollTo(count - 1, anchor: .bottom)
                }
            }
            .background(Color(nsColor: .textBackgroundColor))
        }
        .padding(12)
    }
}
