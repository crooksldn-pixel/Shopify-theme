import Foundation

// SHOW ONLY WHAT MATTERS NOW.
//
// The first CROOKS Control was rejected on sight, and the rejection was right. It worked — every
// control on it did what it said — and it looked like a developer utility: seven integrations in
// an admin table, ten buttons visible at once, a development Mac labelled DEGRADED in the same
// red a broken one would get, and no answer at all to the only three questions the owner
// actually has when he walks up to it.
//
//     1. Is CROOKS OS ready?
//     2. Is CROOKS Pad connected and showing?
//     3. What is the one thing I can usefully do right now?
//
// This file answers those three, and the answer is ONE SCREEN PER STATE rather than one screen
// with everything on it. A capability existing does not earn it permanent space: START, STOP,
// RESTART, HEALTH, START TEST, STOP TEST, OPEN REPORT, CHECK UPDATE, INSTALL UPDATE and ROLLBACK
// were all on screen at once, so none of them was the answer to anything.
//
// WHY THIS IS IN THE CORE AND NOT IN THE VIEW
//
// Because it is a decision, and decisions live here where a test can drive them from a real
// document — the same rule that put the lifecycle verdict and the pad verdict here. "Which word,
// which colour, which single action" is exactly the kind of judgement that can be wrong in a way
// nobody notices, and it is the kind that cannot be checked at all on a machine with no SwiftUI.
// The view that draws this does no branching of its own.

/// What a screen's colour MEANS. Deliberately not `Health`: this is about attention, not health.
public enum Attention: String, Equatable {
    /// Nothing is wrong. Healthy systems recede — this is the quietest thing on the screen.
    case calm
    /// Working, and the expected case. Carries at most one small mark.
    case well
    /// Something wants looking at and nothing has failed. AMBER.
    case attention
    /// Something has actually failed. RED, and unmistakable.
    case failure
    /// Something is happening and there is nothing to do but watch.
    case working
}

/// How an action is drawn, which is a statement about what pressing it means.
public enum Emphasis: String, Equatable {
    /// The one unambiguous thing to press. Bone-filled.
    ///
    /// Not a colour, and that is the point. An appliance that is broken must not spend GREEN on
    /// its recovery button, and a finished test is not a success worth congratulating: prominence
    /// and approval are different things and only the first one is wanted. It is also why a
    /// failure's remedy is bone and not red — the word above is already unmistakable, and
    /// painting the way out in the failure's own colour makes the one thing that helps look like
    /// the one thing to avoid.
    case primary
    /// Available, and nothing is riding on it. An outline on a calm screen.
    case quiet
    /// Deliberate interruption of something that is running. AMBER.
    case caution
    /// Destructive or irreversible.
    case danger
}

public struct ScreenAction: Equatable, Identifiable {
    public let id: String
    public let label: String
    public let emphasis: Emphasis

    public init(id: String, label: String, emphasis: Emphasis) {
        self.id = id
        self.label = label
        self.emphasis = emphasis
    }
}

/// The tablet, as one quiet row — or nothing at all.
/// The environment chip, when this Mac is not the real thing.
public struct ScreenEnvironment: Equatable {
    public let name: String
    public let detail: String

    public init(name: String, detail: String) {
        self.name = name
        self.detail = detail
    }
}

public struct ScreenPad: Equatable {
    public let word: String
    public let detail: String
    public let health: Health

    public init(word: String, detail: String, health: Health) {
        self.word = word
        self.detail = detail
        self.health = health
    }
}

/// WHAT IS ACTUALLY ON THE SCREEN. Everything else the dashboard knows is reachable and none of
/// it is drawn.
public struct Screen: Equatable {
    /// Small caps above the word, when the word alone would not say what this is.
    public let eyebrow: String?
    /// THE ANSWER, and the largest thing on the screen by a long way.
    public let word: String
    /// True when `word` is a figure rather than a word, so it is set in tabular numerals.
    public let wordIsFigure: Bool
    public let attention: Attention
    /// One line of supporting fact under the word.
    public let line: String
    /// A sentence, when there is something the owner needs told. Usually nil.
    public let note: String?
    /// The environment, when this Mac is not the real thing. §10: named BESIDE the word, never
    /// instead of it.
    public let environment: ScreenEnvironment?
    public let pad: ScreenPad?
    /// The stages of something in flight. While these are shown there is nothing to press.
    public let stages: [Stage]
    /// THE one action. At most one.
    public let primary: ScreenAction?
    /// Everything else that is reachable from here, drawn as small text in the footer.
    public let secondary: [ScreenAction]
    public let version: String
    public let build: String

    public init(eyebrow: String? = nil, word: String, wordIsFigure: Bool = false,
                attention: Attention, line: String, note: String? = nil,
                environment: ScreenEnvironment? = nil, pad: ScreenPad? = nil,
                stages: [Stage] = [], primary: ScreenAction? = nil,
                secondary: [ScreenAction] = [], version: String = "", build: String = "") {
        self.eyebrow = eyebrow
        self.word = word
        self.wordIsFigure = wordIsFigure
        self.attention = attention
        self.line = line
        self.note = note
        self.environment = environment
        self.pad = pad
        self.stages = stages
        self.primary = primary
        self.secondary = secondary
        self.version = version
        self.build = build
    }
}

/// A test that has just been stopped, and what it found.
///
/// This is APP state and not document state, which is why it is passed in rather than read out
/// of the status document: the Mac does not know that the owner pressed STOP a moment ago and is
/// still looking at the result. The same split as `busy` and the update verdict — the document is
/// the Mac, and this is what the app knows that the Mac does not.
public struct FinishedTest: Equatable {
    public let id: String
    public let name: String
    public let duration: TimeInterval
    public let interactions: Int
    public let issues: Int

    public init(id: String, name: String, duration: TimeInterval, interactions: Int, issues: Int) {
        self.id = id
        self.name = name
        self.duration = duration
        self.interactions = interactions
        self.issues = issues
    }
}

public enum Presentation {

    /// System Details is a disclosure inside this app, not a command, so it is the one entry
    /// here that does not have to exist in the actions document.
    private static let details = ScreenAction(id: "details", label: "System Details", emphasis: .quiet)

    /// INVARIANT 12, and the reason this takes the dashboard rather than inventing ids.
    ///
    /// "No fake UI or control may be shown if the server cannot perform it." A screen that draws
    /// START on a script with no start action is a lie, and so is one that draws RELOAD THE
    /// TABLET when nothing on this Mac can reload the tablet — which is what the first draft of
    /// this file did, with an id no control script has ever offered.
    ///
    /// So the label and the emphasis are this file's; whether the button exists at all is the
    /// document's. A control that is absent or disabled returns nil, the screen composes without
    /// it, and the sentence above has to carry the owner instead.
    static func pick(_ dashboard: Dashboard, _ id: String, _ label: String,
                     _ emphasis: Emphasis) -> ScreenAction? {
        let offered = dashboard.groups.flatMap(\.buttons).first { $0.id == id }
        guard let offered, offered.enabled else { return nil }
        return ScreenAction(id: id, label: label, emphasis: emphasis)
    }

    /// Compose the one screen. ORDER IS THE LOGIC: the things that own the whole window come
    /// first, and the optional ones come last, because a screen that offers an update while the
    /// backend is down has put the wrong question in front of the owner.
    public static func screen(_ dashboard: Dashboard, status: StatusDocument?,
                              finished: FinishedTest? = nil, now: Date) -> Screen {
        let version = status?.build.current?.version ?? ""
        let build = status?.build.current?.short ?? ""
        let env = environmentChip(status)

        func compose(eyebrow: String? = nil, word: String, figure: Bool = false,
                     attention: Attention, line: String, note: String? = nil,
                     pad: ScreenPad? = nil, stages: [Stage] = [],
                     primary: ScreenAction? = nil, secondary: [ScreenAction] = []) -> Screen {
            Screen(eyebrow: eyebrow, word: word, wordIsFigure: figure, attention: attention,
                   line: line, note: note, environment: env, pad: pad, stages: stages,
                   primary: primary, secondary: secondary + [details],
                   version: version, build: build)
        }

        // ---- An update in flight owns the window. There is nothing to press and nothing else
        // ---- worth reading while it runs, so nothing else is drawn.
        if dashboard.busy != nil, !dashboard.update.stages.isEmpty {
            return compose(word: "UPDATING", attention: .working,
                           line: dashboard.update.sentence, stages: dashboard.update.stages)
        }
        if case .failed(let reason, let rollbackExpected, _) = dashboard.update.verdict {
            return compose(word: "UPDATE FAILED", attention: .failure,
                           line: dashboard.update.headline, note: reason,
                           primary: rollbackExpected
                               ? pick(dashboard, "rollback", "ROLL BACK", .primary)
                               : pick(dashboard, "update", "TRY AGAIN", .primary),
                           secondary: [pick(dashboard, "logs", "Open logs", .quiet)].compactMap { $0 })
        }

        // ---- A test running owns it too, for the same reason. The CLOCK is the hero, not the
        // ---- words "physical test": while one is going, how long it has been going is the fact
        // ---- the owner wants off this screen at a glance.
        if dashboard.session.active {
            let facts = [dashboard.session.name.isEmpty ? dashboard.session.id : dashboard.session.name,
                         dashboard.pad.isReady ? "Pad connected" : dashboard.pad.word.lowercased()]
            // The elapsed time, or the name if this script is too old to send one. A clock
            // reading 00:00 over a test that has been going an hour is worse than no clock.
            let elapsed = status?.testSession.elapsed(now: now)
            return compose(eyebrow: "PHYSICAL TEST",
                           word: elapsed == nil ? "RECORDING" : Format.clock(elapsed),
                           figure: elapsed != nil, attention: .working,
                           line: facts.filter { !$0.isEmpty }.joined(separator: " · "),
                           primary: pick(dashboard, "session_stop", "STOP & ANALYSE", .caution))
        }

        // ---- The Mac itself. Stopped and broken come before anything optional.
        switch dashboard.lifecycle {
        case .offline:
            return compose(word: "OFFLINE", attention: .failure,
                           line: "CROOKS OS is not running on this Mac.",
                           primary: pick(dashboard, "start", "START CROOKS OS", .primary))
        case .starting, .stopping:
            return compose(word: dashboard.lifecycle == .starting ? "STARTING" : "STOPPING",
                           attention: .working, line: dashboard.explanation)
        case .error:
            return compose(word: "NOT WORKING", attention: .failure,
                           line: "CROOKS OS cannot do its job.", note: dashboard.explanation,
                           primary: pick(dashboard, "restart", "RESTART CROOKS OS", .primary),
                           secondary: [pick(dashboard, "logs", "Open logs", .quiet)].compactMap { $0 })
        case .unknown:
            return compose(word: "READING", attention: .working, line: dashboard.explanation)
        case .online:
            break
        }

        // ---- Online, and an essential is down: running and unable to work is its own state, and
        // ---- it is not the same as stopped.
        let down = (status?.issues ?? []).filter { !$0.isEmpty }
        if !down.isEmpty {
            return compose(word: "NOT WORKING", attention: .failure,
                           line: "CROOKS OS is running and cannot do its job.",
                           note: status?.why,
                           primary: pick(dashboard, "restart", "RESTART CROOKS OS", .primary),
                           secondary: [pick(dashboard, "logs", "Open logs", .quiet)].compactMap { $0 })
        }

        // ---- A report waiting to be read.
        if let finished {
            let issues = finished.issues
            return compose(word: "TEST COMPLETE", attention: .calm,
                           line: "\(issues) owner \(issues == 1 ? "issue" : "issues") recorded",
                           note: [finished.name, Format.clock(finished.duration),
                                  "\(finished.interactions) interactions"]
                               .filter { !$0.isEmpty }.joined(separator: " · "),
                           primary: pick(dashboard, "report_open", "OPEN REPORT", .primary),
                           secondary: [pick(dashboard, "session_start", "Run another test", .quiet)].compactMap { $0 })
        }

        // ---- An update on offer. QUIET, not amber: nothing is wrong, and an appliance that
        // ---- lights a warning light because a newer build exists has spent the colour it needs
        // ---- for the day something is actually the matter.
        if case .available = dashboard.update.verdict {
            return compose(word: "UPDATE READY", attention: .calm,
                           line: dashboard.update.sentence,
                           pad: padRow(dashboard.pad),
                           primary: pick(dashboard, "update", "INSTALL UPDATE", .primary),
                           secondary: [pick(dashboard, "session_start", "Start physical test", .quiet)].compactMap { $0 })
        }

        // ---- Working. The TABLET decides what the one action should be.
        let healthy = env == nil ? "Mac online · all systems healthy"
                                 : "Mac online · required systems healthy"
        if dashboard.pad.isBlank {
            // The state the old build could not say at all: the tablet is on, checking in, and
            // showing a white rectangle. The Mac really is well, so the word stays READY and the
            // sentence does not also claim that everything is.
            return compose(word: "READY", attention: .attention, line: "Mac online · CROOKS OS healthy",
                           // NO BUTTON, because there is no control on this Mac that can reload
                           // the tablet's screen — the fix is on the tablet, in the owner's hand.
                           // Drawing one would be invariant 12 broken by this very file.
                           note: "CROOKS OS is well. The tablet is on and not showing CROOKS. "
                               + "Wake the tablet and let CROOKS Pad load again.",
                           pad: padRow(dashboard.pad),
                           secondary: [pick(dashboard, "session_start", "Start physical test", .quiet)].compactMap { $0 })
        }
        return compose(word: "READY", attention: .well, line: healthy, pad: padRow(dashboard.pad),
                       // Quiet, not filled. Nothing is wrong, so nothing needs prominence: a
                       // loud button on a calm screen is the appliance asking for attention it
                       // has not earned.
                       primary: pick(dashboard, "session_start", "START PHYSICAL TEST", .quiet),
                       secondary: [pick(dashboard, "restart", "Restart CROOKS OS", .quiet)].compactMap { $0 })
    }

    static func padRow(_ pad: PadCard) -> ScreenPad {
        ScreenPad(word: pad.word, detail: pad.detail, health: pad.health)
    }

    static func environmentChip(_ status: StatusDocument?) -> ScreenEnvironment? {
        guard let environment = status?.environment, !environment.isReal else { return nil }
        return ScreenEnvironment(name: environment.name.uppercased(), detail: environment.detail)
    }
}
