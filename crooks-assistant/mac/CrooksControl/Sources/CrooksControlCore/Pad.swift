import Foundation

// IS THE TABLET CONNECTED? — the second question the first viewport answers.
//
// There is a trap in it, and the brief names it (§26): "tablet connected vs backend merely
// reachable". The status document carries a Tailscale route — a hostname the Mac is serving
// the pad's page on. It is tempting to draw that as "CROOKS Pad: connected", because it is
// green, it is there, and it changes when things change.
//
// It is not the same fact. The route says a DOOR IS OPEN. It says nothing about whether the
// Samsung is switched on, whether it is in the shop or in a drawer, whether it is on the same
// network, or whether the CROOKS Pad app is running on it. Every one of those can be false
// with the route still green. An owner who reads "connected" and walks away from a tablet
// that has been off since Tuesday has been lied to by his own control panel.
//
// So the only thing that counts as connected is the pad ITSELF having checked in recently,
// and if the control script does not report that, this says so in words rather than guessing.

public enum PadPresence: Equatable {
    /// The pad checked in within living memory. The only case that may be drawn as connected.
    case connected(lastSeen: Date, agent: String)
    /// The pad has checked in before, but not lately. Still a fact worth having — "last seen
    /// 40 minutes ago" is how the owner knows it is in a drawer rather than broken.
    case idle(lastSeen: Date, agent: String)
    /// It has been long enough that it is not there.
    case away(lastSeen: Date)
    /// There is a route, but nothing has ever come through it.
    case neverSeen
    /// There is no route at all: Tailscale is not serving the page, so the pad could not reach
    /// this Mac even if it wanted to.
    case noRoute(note: String)
    /// The honest case. The control script on this Mac does not report the pad's own check-in,
    /// so this app cannot tell — and says so instead of showing the route and calling it
    /// connection.
    case cannotTell(route: String, note: String)

    public var isConnected: Bool {
        if case .connected = self { return true }
        return false
    }

    /// What is drawn under "CROOKS PAD".
    public var word: String {
        switch self {
        case .connected: return "CONNECTED"
        case .idle: return "IDLE"
        case .away: return "DISCONNECTED"
        case .neverSeen: return "NEVER CONNECTED"
        case .noRoute: return "NO ROUTE"
        case .cannotTell: return "NOT REPORTED"
        }
    }

    public var health: Health {
        switch self {
        case .connected: return .ok
        case .idle: return .off
        case .away, .neverSeen: return .bad
        case .noRoute: return .bad
        // Not knowing is not a fault, and it must not be drawn as one — but it must not be
        // drawn as health either.
        case .cannotTell: return .notReported
        }
    }
}

/// WHAT IS ON THE TABLET'S SCREEN — and it is a different question from whether the tablet is
/// there, which is what `PadPresence` answers.
///
/// The brief names three facts and they come apart in exactly this order:
///
///   * the transport is connected   — the tablet checked in            (`PadPresence`)
///   * the web surface is loaded    — its WebView came up              (`webview`)
///   * CROOKS OS is actually showing — and is what the owner is seeing  (`showingCrooks`)
///
/// The second and third are what the pad itself reports and nothing else can observe. A tablet
/// whose renderer has crashed goes on checking in perfectly happily: every transport fact stays
/// green while the owner looks at a white rectangle. That is the fake green this layer exists to
/// prevent, and for most of Phase 6 it was unpreventable here, because `showing_crooks` was
/// dropped by the hop between the backend and the control script and never reached this app.
public enum PadSurface: Equatable {
    /// The pad says CROOKS is on the screen.
    case showing
    /// Coming up. Not showing yet, and not a fault.
    case loading
    /// The pad says it is NOT showing, and names what went wrong: `error` or `crashed`.
    case blank(String)
    /// The pad has not said. NOT "no" — an unanswered question drawn as a failure is how a
    /// status screen teaches its owner to stop reading it.
    case notSaid

    public static func read(_ pad: PadReport) -> PadSurface {
        switch pad.webview.lowercased() {
        case "loaded": return .showing
        case "loading": return .loading
        case "error", "crashed": return .blank(pad.webview.lowercased())
        default:
            // No word for the surface. `showing_crooks` may still carry the answer, and a
            // `false` with nothing naming the cause is still a blank screen.
            guard let showing = pad.showingCrooks else { return .notSaid }
            return showing ? .showing : .blank("")
        }
    }
}

/// The two facts together, which is the only way either of them is safe to draw.
///
/// `PadPresence` on its own answers "is the tablet there", and every caller that drew that word
/// alone was making a claim about the product — CONNECTED, in green — out of a fact about the
/// network. This type is what the views read, so that claim cannot be made by accident.
public struct PadState: Equatable {
    public let presence: PadPresence
    public let surface: PadSurface

    public init(presence: PadPresence, surface: PadSurface) {
        self.presence = presence
        self.surface = surface
    }

    /// The tablet is there AND CROOKS is on it. The only combination the appliance is actually
    /// doing its job in, and the only one this app may present as everything being well.
    public var isReady: Bool {
        presence.isConnected && surface == .showing
    }

    /// The tablet is there and CROOKS is NOT on it. The state that used to be indistinguishable
    /// from working.
    public var isBlank: Bool {
        guard presence.isConnected else { return false }
        if case .blank = surface { return true }
        return false
    }

    /// What is drawn under "CROOKS PAD". CONNECTED is reserved for a pad that is connected AND
    /// not known to be blank — it is a claim about CROOKS, not about the socket.
    public var word: String {
        guard presence.isConnected else { return presence.word }
        switch surface {
        case .showing, .notSaid: return "CONNECTED"
        case .loading: return "LOADING"
        case .blank: return "NOT SHOWING"
        }
    }

    public var health: Health {
        guard presence.isConnected else { return presence.health }
        switch surface {
        case .showing, .notSaid: return presence.health
        // Mid-load is not a fault and not health either.
        case .loading: return .off
        case .blank: return .bad
        }
    }

    public func detail(route: StatusDocument.TabletRoute, now: Date) -> String {
        let base = PadReading.detail(presence, route: route, now: now)
        guard presence.isConnected else { return base }
        switch surface {
        case .showing, .notSaid: return base
        case .loading: return base + ". The screen is still loading."
        case .blank(let why):
            let named = why.isEmpty ? "" : " (\(why))"
            return "The tablet is here and CROOKS is not on its screen\(named). " + base
        }
    }
}

public enum PadReading {
    /// How fresh a check-in has to be to count as connected.
    ///
    /// The pad polls /health while its screen is on. A minute and a half covers a slow poll
    /// and a moment of bad wifi without covering a tablet that has been put down.
    public static let connected: TimeInterval = 90
    /// Beyond this it is not idle, it is gone.
    public static let idle: TimeInterval = 15 * 60

    public static func read(_ status: StatusDocument, now: Date) -> PadPresence {
        let route = status.tablet.host
        let note = status.tablet.note

        guard let pad = status.pad else {
            // No heartbeat in this build of the control script. Say which of the two facts we
            // actually have, and do not let the one we have stand in for the one we do not.
            if route.isEmpty {
                return .noRoute(note: note.isEmpty ? "Tailscale is not serving the CROOKS Pad's address." : note)
            }
            return .cannotTell(
                route: status.tablet.url.isEmpty ? route : status.tablet.url,
                note: "CROOKS OS on this Mac reports the address the pad would use, but not whether the pad "
                    + "has used it. A route is an open door, not a tablet on the other side of it."
            )
        }

        // `known: false` is the script being too old to ask, which is ignorance and not absence.
        // It gets the same answer as no pad block at all.
        guard pad.known else {
            if route.isEmpty { return .noRoute(note: note.isEmpty ? "Tailscale is not serving the CROOKS Pad's address." : note) }
            return .cannotTell(route: status.tablet.url.isEmpty ? route : status.tablet.url,
                               note: pad.detail.isEmpty ? "This build does not report the tablet's own check-in." : pad.detail)
        }
        // The script reports the pad but will not say whether it is alive. Still not a guess.
        guard let alive = pad.alive else {
            if route.isEmpty { return .noRoute(note: note) }
            return .cannotTell(route: status.tablet.url.isEmpty ? route : status.tablet.url,
                               note: pad.detail.isEmpty ? "The tablet has been seen, but this build does not say when." : pad.detail)
        }
        // LIVENESS IS THE SCRIPT'S VERDICT, not ours. It makes it against the backend's own
        // staleness window, and the backend is the one holding the socket; a second opinion here
        // is how the Mac and this app come to draw different colours over the same tablet. `age`
        // is used only to say how long it has been, and to tell a tablet put down a minute ago
        // from one that has been off since Tuesday.
        //
        // A negative age (the Mac woke and re-synced its clock) must not read as a check-in from
        // the future, so it is floored at zero rather than trusted.
        let age = max(0, pad.ageS ?? 0)
        let lastSeen = now.addingTimeInterval(-age)
        if alive { return .connected(lastSeen: lastSeen, agent: pad.app) }
        guard pad.ageS != nil else {
            if route.isEmpty { return .noRoute(note: note) }
            return .neverSeen
        }
        if age <= idle { return .idle(lastSeen: lastSeen, agent: pad.app) }
        return .away(lastSeen: lastSeen)
    }

    /// Both facts, which is what the views read. Drawing `read(_:now:)` alone is what turned a
    /// statement about the network into a claim about CROOKS.
    public static func state(_ status: StatusDocument, now: Date) -> PadState {
        PadState(presence: read(status, now: now),
                 surface: status.pad.map(PadSurface.read) ?? .notSaid)
    }

    /// The line under the word. This is where "last seen" lives, and where the route is shown
    /// as what it is.
    public static func detail(_ presence: PadPresence, route: StatusDocument.TabletRoute, now: Date) -> String {
        switch presence {
        case .connected(let lastSeen, let agent):
            let who = agent.isEmpty ? "" : "\(agent) · "
            return who + "last heard from " + Format.ago(lastSeen, now: now)
        case .idle(let lastSeen, let agent):
            let who = agent.isEmpty ? "" : "\(agent) · "
            return who + "last heard from " + Format.ago(lastSeen, now: now) + ". The screen is probably off."
        case .away(let lastSeen):
            return "Last heard from " + Format.ago(lastSeen, now: now)
                + ". Wake the tablet, or check it is on the same network."
        case .neverSeen:
            return "The address is being served, but the CROOKS Pad has never used it. "
                + "Install CROOKS Pad on the tablet, or open \(route.url) on it once."
        case .noRoute(let note):
            return note.isEmpty
                ? "The tablet has no way to reach this Mac. Check Tailscale is running."
                : note
        case .cannotTell(let route, let note):
            return "\(route) — \(note)"
        }
    }
}
