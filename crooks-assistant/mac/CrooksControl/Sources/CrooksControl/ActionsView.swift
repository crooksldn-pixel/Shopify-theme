import SwiftUI
import CrooksControlCore

// The controls. Drawn from whatever `crooks-control actions` lists, in the groups and the
// order the core put them in, with the weight the core gave each one.
//
// The three rules this view follows and does not decide:
//
//   * a dangerous action is a different shape, not just a different colour, and it never sits
//     shoulder to shoulder with a harmless one in a way that lets a stray click land wrong;
//   * a disabled button says why, under itself, and is never merely inert;
//   * a control the script does not offer is not drawn at all.

struct ActionsView: View {
    let groups: [ActionGroup]
    let missing: [String]
    let press: (ActionButton) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            ForEach(groups) { group in
                VStack(alignment: .leading, spacing: 10) {
                    Text(group.title.uppercased())
                        .font(.system(size: 10, weight: .bold)).tracking(1.2)
                        .foregroundStyle(Ink.quaternary)
                    FlowRow(spacing: 8) {
                        ForEach(group.buttons) { button in
                            ActionChip(button: button, press: press)
                        }
                    }
                }
            }
            // INVARIANT 12, SAID OUT LOUD. A control the script cannot perform is not drawn —
            // that part was already true, because the buttons are built from the document. But
            // not drawing it silently leaves the owner in front of a panel with no START button
            // and no reason, which is its own kind of dead end. MAC_CONTROL.md promises "there
            // is no START button AND THE APP SAYS SO IN WORDS", and this is the words.
            //
            // The core has supplied this list all along and this view took it as a parameter and
            // never read it — invariant 12 as decoration in the view layer, the same shape of
            // defect as the missing-controls list that was declared, supplied and never read one
            // layer down. The notice above surfaces at most ONE of these, and only when it
            // outranks everything else competing for that slot; everything else went unsaid.
            if !missing.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("NOT AVAILABLE")
                        .font(.system(size: 10, weight: .bold)).tracking(1.2)
                        .foregroundStyle(Signal.warn)
                    Text(missing.joined(separator: " · "))
                        .font(.system(size: 12.5, weight: .medium))
                        .foregroundStyle(Ink.secondary)
                    Text("CROOKS OS on this Mac does not offer "
                         + (missing.count == 1 ? "this control" : "these controls")
                         + ". Rebuild CROOKS Control from this checkout to get "
                         + (missing.count == 1 ? "it" : "them") + " back.")
                        .font(.system(size: 11))
                        .foregroundStyle(Ink.quaternary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(.horizontal, 14).padding(.vertical, 11)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: Radius.control, style: .continuous)
                        .fill(Signal.warn.opacity(0.10))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.control, style: .continuous)
                        .strokeBorder(Signal.warn.opacity(0.35), lineWidth: 1)
                )
            }
        }
    }
}

struct ActionChip: View {
    let button: ActionButton
    let press: (ActionButton) -> Void

    @State private var asking = false
    @State private var hovering = false

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Button {
                if button.needsConfirmation { asking = true } else { press(button) }
            } label: {
                HStack(spacing: 6) {
                    if button.severity == .danger {
                        Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 9))
                    }
                    Text(button.label).font(.system(size: 12.5, weight: weight))
                }
                .padding(.horizontal, 14).padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: Radius.control, style: .continuous).fill(fill)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: Radius.control, style: .continuous)
                        .strokeBorder(border, lineWidth: 1)
                )
                .foregroundStyle(ink)
            }
            .buttonStyle(.plain)
            .disabled(!button.enabled)
            .onHover { hovering = $0 }
            .help(button.enabled ? button.why : (button.disabledReason ?? button.why))
            .animation(Motion.settle, value: button.enabled)

            // §5.2 and the whole point of the availability rules: a grey button is never a
            // mystery. The reason is drawn, not hidden in a tooltip, for the ones that matter.
            if !button.enabled, let reason = button.disabledReason, button.severity != .normal || hovering {
                Text(reason)
                    .font(.system(size: 10)).foregroundStyle(Ink.quaternary)
                    .frame(maxWidth: 210, alignment: .leading)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .alert(button.label, isPresented: $asking) {
            Button("Cancel", role: .cancel) { asking = false }
            Button(button.label, role: button.severity == .danger ? .destructive : nil) {
                press(button)
                asking = false
            }
        } message: {
            Text(button.confirmText ?? "")
        }
    }

    private var weight: Font.Weight { button.severity == .danger ? .semibold : .medium }

    private var fill: Color {
        guard button.enabled else { return Glass.fill.opacity(0.5) }
        switch button.severity {
        case .danger: return Signal.bad.opacity(hovering ? 0.26 : 0.16)
        case .caution: return Signal.warn.opacity(hovering ? 0.22 : 0.13)
        case .normal: return hovering ? Glass.strong : Glass.fill
        }
    }

    private var border: Color {
        guard button.enabled else { return Glass.lineSubtle }
        switch button.severity {
        case .danger: return Signal.bad.opacity(0.55)
        case .caution: return Signal.warn.opacity(0.45)
        case .normal: return Glass.lineRest
        }
    }

    private var ink: Color {
        guard button.enabled else { return Ink.quaternary }
        switch button.severity {
        case .danger: return Signal.bad
        case .caution: return Signal.warn
        case .normal: return Ink.primary
        }
    }
}

/// Chips that wrap. `LazyVGrid` would give a grid of equal columns, which makes "START" as
/// wide as "Install CROOKS Pad" and the row reads as a table rather than a set of controls.
struct FlowRow: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 480
        let rows = arrange(subviews, in: width)
        let height = rows.reduce(0) { $0 + $1.height } + spacing * CGFloat(max(0, rows.count - 1))
        return CGSize(width: width, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var y = bounds.minY
        for row in arrange(subviews, in: bounds.width) {
            var x = bounds.minX
            for index in row.indices {
                let size = subviews[index].sizeThatFits(.unspecified)
                subviews[index].place(at: CGPoint(x: x, y: y), anchor: .topLeading,
                                      proposal: ProposedViewSize(size))
                x += size.width + spacing
            }
            y += row.height + spacing
        }
    }

    private struct Row {
        var indices: [Int] = []
        var height: CGFloat = 0
    }

    private func arrange(_ subviews: Subviews, in width: CGFloat) -> [Row] {
        var rows: [Row] = []
        var row = Row()
        var x: CGFloat = 0
        for index in subviews.indices {
            let size = subviews[index].sizeThatFits(.unspecified)
            if !row.indices.isEmpty, x + size.width > width {
                rows.append(row)
                row = Row()
                x = 0
            }
            row.indices.append(index)
            row.height = max(row.height, size.height)
            x += size.width + spacing
        }
        if !row.indices.isEmpty { rows.append(row) }
        return rows
    }
}
