import SwiftUI
import CrooksControlCore

// THE FRONT PAGE, and it draws a `Screen` and decides nothing.
//
// Every branch — which word, which colour, which single action, whether the tablet is even worth
// a row right now — was taken in `Presentation.screen(...)`, in the Foundation-only core where a
// test can drive it from a real document. What is left here is layout, which is the same split
// the rest of this app is built on and the only reason any of it could be trusted on a machine
// that cannot compile SwiftUI.
//
// The rejected build put ten controls, seven integrations and a DEGRADED banner on screen at
// once. This draws, at most: a word, a line, a sentence, the tablet, and ONE button.

struct ScreenView: View {
    let screen: Screen
    let press: (ScreenAction) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            bar
            head
            middle
            footer
        }
        .frame(width: 420)
        .background(ground)
        .animation(Motion.settle, value: screen.word)
    }

    // MARK: - The ground

    /// One very soft field behind the word, tinted by what the screen is saying. Depth, not
    /// decoration: without it a near-black panel reads as a hole rather than as a surface.
    private var ground: some View {
        ZStack {
            Ground.base
            RadialGradient(colors: [tone.opacity(0.07), .clear],
                           center: .init(x: 0.5, y: 0.16), startRadius: 4, endRadius: 320)
                .allowsHitTesting(false)
        }
        .ignoresSafeArea()
    }

    private var tone: Color {
        switch screen.attention {
        case .calm, .well: return Signal.ok
        case .attention: return Signal.warn
        case .failure: return Signal.bad
        case .working: return Color(hex: 0x9BB3D4)
        }
    }

    /// The LED is the only colour a calm screen carries, so it is the only thing that has to
    /// change when the appliance does. A healthy system recedes; it does not glow.
    private var lit: Color {
        switch screen.attention {
        case .calm: return Ink.quaternary
        case .well: return Signal.ok
        case .attention: return Signal.warn
        case .failure: return Signal.bad
        case .working: return Color(hex: 0x9BB3D4)
        }
    }

    // MARK: - The bar

    private var bar: some View {
        HStack(spacing: 0) {
            HStack(spacing: 9) {
                Circle().fill(lit).frame(width: 6.5, height: 6.5)
                    .shadow(color: lit.opacity(0.5), radius: 4)
                Text("CROOKS")
                    .font(.system(size: 10.5, weight: .bold)).tracking(2.2)
                    .foregroundStyle(Ink.tertiary)
            }
            Spacer()
            if let environment = screen.environment {
                // §10. Named BESIDE the word and never instead of it: a development Mac whose
                // store is a fixture is doing exactly what it is supposed to, and a panel that
                // shouts DEGRADED at it has taught its owner that its loudest word means nothing.
                HStack(spacing: 6) {
                    Text(environment.name)
                        .font(.system(size: 9, weight: .bold)).tracking(1.4)
                        .foregroundStyle(Signal.warn)
                    if !environment.detail.isEmpty {
                        Text(environment.detail)
                            .font(.system(size: 9)).foregroundStyle(Ink.tertiary)
                    }
                }
                .padding(.horizontal, 9).padding(.vertical, 4)
                .background(Capsule().fill(Signal.warn.opacity(0.10)))
                .overlay(Capsule().strokeBorder(Signal.warn.opacity(0.28), lineWidth: 1))
            }
        }
        .padding(.horizontal, 20).padding(.top, 16)
    }

    // MARK: - The answer

    private var head: some View {
        VStack(alignment: .leading, spacing: 0) {
            if let eyebrow = screen.eyebrow {
                Text(eyebrow)
                    .font(.system(size: 9.5, weight: .bold)).tracking(2)
                    .foregroundStyle(Ink.tertiary)
                    .padding(.bottom, 9)
            }
            Text(screen.word)
                // Tabular figures come off the FONT, not from a `.monospacedDigit()` modifier
                // chained after it: that one returns a view, and `.tracking` is a Text method, so
                // the two cannot sit in the same chain. SF Pro's own numerals are fixed-width and
                // better drawn than any monospaced face would be here.
                .font(wordFont)
                .tracking(screen.wordIsFigure ? -0.9 : -1.1)
                .foregroundStyle(screen.attention == .failure ? Signal.bad : Ink.primary)
                .lineLimit(1).minimumScaleFactor(0.7)
            if !screen.line.isEmpty {
                Text(screen.line)
                    .font(.system(size: 12.5)).foregroundStyle(Ink.tertiary)
                    .padding(.top, 11)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if let note = screen.note {
                Text(note)
                    .font(.system(size: 12)).lineSpacing(2)
                    .foregroundStyle(screen.attention == .failure ? Signal.bad : Ink.secondary)
                    .padding(.top, 9)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20).padding(.top, 26)
    }

    private var wordFont: Font {
        let face = Font.system(size: screen.wordIsFigure ? 46 : 38, weight: .semibold)
        return screen.wordIsFigure ? face.monospacedDigit() : face
    }

    // MARK: - The middle: at most the tablet, or what is in flight

    /// A FIXED gap above this, never a flexible Spacer. A Spacer would grow to whatever height
    /// the window happened to be and put the black void back down the middle of the screen —
    /// which is the single thing the previous build was rejected for. The window is sized to its
    /// content instead, so there is nothing to fill.
    @ViewBuilder private var middle: some View {
        VStack(alignment: .leading, spacing: 14) {
            if !screen.stages.isEmpty { stages }
            if let pad = screen.pad { padRow(pad) }
            if let primary = screen.primary { button(primary) }
        }
        .padding(.horizontal, 20).padding(.top, 20).padding(.bottom, 20)
    }

    private var stages: some View {
        Tray {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(screen.stages.enumerated()), id: \.offset) { index, stage in
                    if index > 0 { Divider().overlay(Glass.lineSubtle.opacity(0.5)) }
                    HStack(spacing: 10) {
                        Circle().fill(stageColour(stage)).frame(width: 5, height: 5)
                        Text(stage.stage)
                            .font(.system(size: 12.5, weight: stage.state == "running" ? .semibold : .regular))
                            .foregroundStyle(stageInk(stage))
                        Spacer()
                    }
                    .padding(.vertical, 9)
                }
            }
            .padding(.horizontal, 12)
        }
    }

    /// Done stages recede; the RUNNING one is the fact. Completed steps turning green would put
    /// three greens on a screen whose only live information is which step is happening now.
    private func stageColour(_ stage: Stage) -> Color {
        switch stage.state {
        case "running": return Color(hex: 0x9BB3D4)
        case "fail": return Signal.bad
        case "ok": return Ink.tertiary
        default: return Ink.quaternary.opacity(0.6)
        }
    }

    private func stageInk(_ stage: Stage) -> Color {
        switch stage.state {
        case "running": return Ink.primary
        case "fail": return Signal.bad
        case "ok": return Ink.secondary
        default: return Ink.quaternary
        }
    }

    private func padRow(_ pad: ScreenPad) -> some View {
        Tray {
            HStack(alignment: .top, spacing: 10) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("CROOKS PAD")
                        .font(.system(size: 9.5, weight: .bold)).tracking(1.8)
                        .foregroundStyle(Ink.quaternary)
                    Text(pad.word)
                        .font(.system(size: 14, weight: .semibold))
                        // CONNECTED is drawn in ink, not green: a working tablet is the expected
                        // case, and the expected case does not need a colour.
                        .foregroundStyle(padInk(pad.health))
                    if !pad.detail.isEmpty {
                        Text(pad.detail)
                            .font(.system(size: 11)).foregroundStyle(Ink.quaternary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                Spacer(minLength: 8)
                Circle().fill(padPip(pad.health)).frame(width: 6.5, height: 6.5)
                    .padding(.top, 3)
            }
            .padding(.horizontal, 14).padding(.vertical, 13)
        }
    }

    private func padInk(_ health: Health) -> Color {
        switch health {
        case .bad: return Signal.bad
        case .off, .notReported: return Ink.secondary
        case .ok: return Ink.primary
        }
    }

    private func padPip(_ health: Health) -> Color {
        switch health {
        case .ok: return Ink.quaternary
        case .off, .notReported: return Ink.quaternary
        case .bad: return Signal.bad
        }
    }

    // MARK: - The one action

    private func button(_ action: ScreenAction) -> some View {
        Button { press(action) } label: {
            HStack(spacing: 10) {
                Text(action.label)
                    .font(.system(size: 13, weight: .semibold)).tracking(1.1)
                Spacer()
                ZStack {
                    Circle().fill(chevronGround(action.emphasis)).frame(width: 24, height: 24)
                    Image(systemName: "chevron.right").font(.system(size: 10, weight: .semibold))
                }
            }
            .foregroundStyle(ink(action.emphasis))
            .padding(.horizontal, 18).padding(.vertical, 15)
            .frame(maxWidth: .infinity)
            .background(RoundedRectangle(cornerRadius: Radius.control + 2, style: .continuous)
                .fill(fill(action.emphasis)))
            .overlay(RoundedRectangle(cornerRadius: Radius.control + 2, style: .continuous)
                .strokeBorder(border(action.emphasis), lineWidth: 1))
        }
        .buttonStyle(PressableButtonStyle())
    }

    private func fill(_ emphasis: Emphasis) -> Color {
        switch emphasis {
        case .primary: return Ink.primary
        case .quiet: return Ground.three
        case .caution: return Signal.warn.opacity(0.13)
        case .danger: return Signal.bad.opacity(0.14)
        }
    }

    private func border(_ emphasis: Emphasis) -> Color {
        switch emphasis {
        case .primary: return Ink.primary
        case .quiet: return Glass.lineRest
        case .caution: return Signal.warn.opacity(0.36)
        case .danger: return Signal.bad.opacity(0.40)
        }
    }

    private func ink(_ emphasis: Emphasis) -> Color {
        switch emphasis {
        case .primary: return Ground.base
        case .quiet: return Ink.primary
        case .caution: return Color(hex: 0xF0DCB2)
        case .danger: return Color(hex: 0xF2C4B9)
        }
    }

    private func chevronGround(_ emphasis: Emphasis) -> Color {
        emphasis == .primary ? Ground.base.opacity(0.12) : Color.white.opacity(0.07)
    }

    // MARK: - Everything else, receding

    private var footer: some View {
        HStack(spacing: 0) {
            Text(screen.build.isEmpty ? screen.version : "\(screen.version) · \(screen.build)")
                .font(.system(size: 10.5, design: .monospaced))
                .foregroundStyle(Ink.quaternary)
            Spacer()
            HStack(spacing: 14) {
                ForEach(screen.secondary) { action in
                    Button(action.label) { press(action) }
                        .buttonStyle(.plain)
                        .font(.system(size: 10.5))
                        .foregroundStyle(Ink.tertiary)
                }
            }
        }
        .padding(.horizontal, 20).padding(.vertical, 12)
        .overlay(alignment: .top) { Rectangle().fill(Glass.lineSubtle).frame(height: 1) }
    }
}

/// A physical press: the control moves under the finger and comes back.
struct PressableButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(Motion.settle, value: configuration.isPressed)
            .contentShape(Rectangle())
    }
}

/// The double bezel: an outer tray with a hairline, an inner plate with its own top highlight.
/// A card laid flat on the ground reads as a rectangle of slightly different black; this reads
/// as a plate sitting in a tray, which is what makes the panel feel like a made object.
struct Tray<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: Radius.control - 3, style: .continuous)
                .fill(Ground.two))
            .overlay(RoundedRectangle(cornerRadius: Radius.control - 3, style: .continuous)
                .strokeBorder(Color.white.opacity(0.05), lineWidth: 1))
            .padding(4)
            .background(RoundedRectangle(cornerRadius: Radius.control + 1, style: .continuous)
                .fill(Ground.one))
            .overlay(RoundedRectangle(cornerRadius: Radius.control + 1, style: .continuous)
                .strokeBorder(Glass.lineSubtle, lineWidth: 1))
    }
}
