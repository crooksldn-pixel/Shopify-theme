import XCTest
@testable import CrooksControlCore

/// "tablet connected vs backend merely reachable" (§26), which is the whole of this file.
final class PadTests: XCTestCase {

    let now = Date(timeIntervalSince1970: 1_789_000_000)

    func status(_ data: Data) throws -> StatusDocument {
        try Contract.decoder.decode(StatusDocument.self, from: data)
    }

    /// The online fixture with a pad block bolted on, IN THE SHAPE `crooks-control status`
    /// ACTUALLY PRINTS.
    ///
    /// This helper used to emit `{"seen_at": …, "agent": …, "address": …}`. No control script has
    /// ever printed those keys — `pad_status()` prints
    /// `{known, alive, age_s, app, version, build, source, detail, showing_crooks, webview}`, and
    /// says so in its own contract. So every test below was passing against a document the
    /// product cannot produce, while against the real one `PadReport.seenAt` was nil and the app
    /// answered NEVER CONNECTED for a working tablet.
    ///
    /// A fixture written from the reader proves the reader. Only a fixture written from the
    /// document proves the contract.
    func withPad(alive: Bool?, ageS: Double?, known: Bool = true,
                 app: String = "crooks-pad 1.4.0 (SM-T290)",
                 webview: String = "loaded", showingCrooks: Bool? = true,
                 detail: String = "") throws -> StatusDocument {
        var raw = try XCTUnwrap(String(data: Fixture.onlineStatus, encoding: .utf8))
        let aliveJSON = alive.map { $0 ? "true" : "false" } ?? "null"
        let ageJSON = ageS.map { "\($0)" } ?? "null"
        let showingJSON = showingCrooks.map { $0 ? "true" : "false" } ?? "null"
        raw = raw.replacingOccurrences(
            of: "\"port\": 8000",
            with: "\"port\": 8000,\n  \"pad\": {\"known\": \(known ? "true" : "false"), "
                + "\"alive\": \(aliveJSON), \"age_s\": \(ageJSON), \"app\": \"\(app)\", "
                + "\"version\": \"1.4.0\", \"build\": \"1.4.0\", \"source\": \"pad\", "
                + "\"detail\": \"\(detail)\", \"showing_crooks\": \(showingJSON), "
                + "\"webview\": \"\(webview)\"}"
        )
        return try status(Data(raw.utf8))
    }

    // MARK: - The trap

    func testARouteOnItsOwnIsNeverDrawnAsConnected() throws {
        // The status document has a Tailscale host. Everything is GREEN. The tablet could
        // still be switched off in a drawer, and nothing in this document would say so.
        let document = try status(Fixture.onlineStatus)
        XCTAssertFalse(document.tablet.host.isEmpty, "there IS a route — that is the trap")
        XCTAssertNil(document.pad, "and no heartbeat, because this build does not send one")

        let presence = PadReading.read(document, now: now)
        XCTAssertFalse(presence.isConnected)
        guard case .cannotTell = presence else {
            return XCTFail("a route must read as “cannot tell”, got \(presence)")
        }
        XCTAssertEqual(presence.word, "NOT REPORTED")
        XCTAssertEqual(presence.health, .notReported,
                       "not knowing is not a fault — but it is not health either")

        let detail = PadReading.detail(presence, route: document.tablet, now: now)
        XCTAssertTrue(detail.contains("open door"),
                      "the owner is told exactly what the green thing means: \(detail)")
    }

    func testNoRouteAtAllIsItsOwnAnswer() throws {
        let document = try status(Fixture.noRouteStatus)
        let presence = PadReading.read(document, now: now)
        guard case .noRoute = presence else { return XCTFail("expected noRoute, got \(presence)") }
        XCTAssertEqual(presence.health, .bad)
        XCTAssertEqual(presence.word, "NO ROUTE")
    }

    // MARK: - A real heartbeat

    func testAFreshCheckInIsConnected() throws {
        let document = try withPad(alive: true, ageS: 12)
        let presence = PadReading.read(document, now: now)
        XCTAssertTrue(presence.isConnected)
        XCTAssertEqual(presence.health, .ok)
        let detail = PadReading.detail(presence, route: document.tablet, now: now)
        XCTAssertTrue(detail.contains("SM-T290"), detail)
        XCTAssertTrue(detail.contains("ago"), "§5 asks for last seen: \(detail)")
    }

    func testACheckInFromFourMinutesAgoIsIdleNotConnected() throws {
        let document = try withPad(alive: false, ageS: 240)
        let presence = PadReading.read(document, now: now)
        XCTAssertFalse(presence.isConnected)
        XCTAssertEqual(presence.word, "IDLE")
        XCTAssertTrue(PadReading.detail(presence, route: document.tablet, now: now).contains("4m ago"))
    }

    func testACheckInFromYesterdayIsDisconnectedAndSaysWhen() throws {
        let document = try withPad(alive: false, ageS: 86_400)
        let presence = PadReading.read(document, now: now)
        XCTAssertEqual(presence.word, "DISCONNECTED")
        XCTAssertEqual(presence.health, .bad)
        let detail = PadReading.detail(presence, route: document.tablet, now: now)
        XCTAssertTrue(detail.contains("24.0h ago"), detail)
        XCTAssertTrue(detail.lowercased().contains("wake"), "say what to do: \(detail)")
    }

    func testARouteThatHasNeverBeenUsed() throws {
        let document = try withPad(alive: false, ageS: nil, showingCrooks: nil, detail: "never")
        let presence = PadReading.read(document, now: now)
        XCTAssertEqual(presence.word, "NEVER CONNECTED")
        XCTAssertTrue(PadReading.detail(presence, route: document.tablet, now: now)
            .contains("Install CROOKS Pad"))
    }

    func testThisAppKeepsNoSecondOpinionAboutWhenAPadIsStale() throws {
        // The staleness window belongs to the BACKEND — it is the one holding the socket — and
        // the control script applies it. This app used to apply its own ninety seconds on top,
        // which is how the Mac and the app come to draw different colours over one tablet.
        //
        // So a script that says alive is believed, even at an age this side would have called
        // stale; and a script that says stale is believed, even at an age this side would have
        // called fresh.
        let oldButAlive = try withPad(alive: true, ageS: PadReading.connected + 300)
        XCTAssertTrue(PadReading.read(oldButAlive, now: now).isConnected,
                      "the script's verdict wins over this side's arithmetic")
        let freshButStale = try withPad(alive: false, ageS: 5)
        XCTAssertFalse(PadReading.read(freshButStale, now: now).isConnected)
    }

    func testANegativeAgeIsNotTreatedAsACheckInFromTheFuture() throws {
        // A Mac that woke and re-synced its clock can produce a negative age. Floored at zero:
        // "just now" is the most it may ever mean.
        let document = try withPad(alive: true, ageS: -3600)
        let presence = PadReading.read(document, now: now)
        XCTAssertTrue(presence.isConnected)
        guard case .connected(let lastSeen, _) = presence else { return XCTFail("expected connected") }
        XCTAssertEqual(lastSeen.timeIntervalSince1970, now.timeIntervalSince1970, accuracy: 0.001,
                       "a negative age is clamped to now, never carried into the future")
    }

    func testAScriptTooOldToReportAHeartbeatIsIgnoranceAndNotAbsence() throws {
        let document = try withPad(alive: nil, ageS: nil, known: false, showingCrooks: nil, webview: "")
        let presence = PadReading.read(document, now: now)
        guard case .cannotTell = presence else { return XCTFail("expected cannotTell, got \(presence)") }
        XCTAssertEqual(presence.health, .notReported, "not knowing is not a fault")
    }

    // MARK: - CONNECTED is not the same claim as CROOKS IS SHOWING

    func testATabletThatIsAliveAndBlankIsNeverDrawnAsConnected() throws {
        // The tablet is on and checking in. Its renderer has crashed, so the owner is looking at
        // a white rectangle. Every transport fact here is green, and for most of Phase 6 that is
        // all this app could see: `showing_crooks` was dropped by the hop out of the backend.
        let document = try withPad(alive: true, ageS: 4, webview: "crashed", showingCrooks: false)
        let state = PadReading.state(document, now: now)
        XCTAssertTrue(state.presence.isConnected, "the tablet really is there")
        XCTAssertEqual(state.surface, .blank("crashed"))
        XCTAssertFalse(state.isReady, "and the appliance is NOT doing its job")
        XCTAssertTrue(state.isBlank)
        XCTAssertEqual(state.word, "NOT SHOWING", "the word may not be CONNECTED")
        XCTAssertEqual(state.health, .bad)
        XCTAssertTrue(state.detail(route: document.tablet, now: now).contains("not on its screen"))
    }

    func testATabletStillLoadingIsNeitherATickNorACross() throws {
        let document = try withPad(alive: true, ageS: 2, webview: "loading", showingCrooks: false)
        let state = PadReading.state(document, now: now)
        XCTAssertEqual(state.surface, .loading)
        XCTAssertEqual(state.word, "LOADING")
        XCTAssertEqual(state.health, .off, "mid-load is not a fault and not health either")
        XCTAssertFalse(state.isReady)
    }

    func testAPadThatHasNotSaidWhatIsOnItsScreenIsNotAccusedOfBeingBlank() throws {
        // The dangerous direction is fake green; this is the other one. A row reading NOT
        // SHOWING CROOKS over a working tablet is how the row gets ignored.
        let document = try withPad(alive: true, ageS: 4, webview: "", showingCrooks: nil)
        let state = PadReading.state(document, now: now)
        XCTAssertEqual(state.surface, .notSaid)
        XCTAssertEqual(state.word, "CONNECTED")
        XCTAssertEqual(state.health, .ok)
        XCTAssertFalse(state.isBlank, "silence is not an accusation")
        XCTAssertFalse(state.isReady, "and it is not a guarantee either")
    }

    func testTheSurfaceIsNotDrawnAtAllWhenTheTabletIsNotThere() throws {
        // What the pad last said about its screen describes a screen nobody is looking at.
        let document = try withPad(alive: false, ageS: 86_400, webview: "loaded", showingCrooks: true)
        let state = PadReading.state(document, now: now)
        XCTAssertEqual(state.word, "DISCONNECTED", "the tablet answers first")
        XCTAssertEqual(state.health, .bad)
        XCTAssertFalse(state.isReady)
    }

    func testTheDashboardCardCarriesBothFacts() throws {
        let document = try withPad(alive: true, ageS: 4, webview: "error", showingCrooks: false)
        var machine = LifecycleMachine()
        machine.observe(.status(document), at: now)
        let dashboard = DashboardBuilder.build(
            DashboardInput(status: document, machine: machine, now: now))
        XCTAssertEqual(dashboard.pad.word, "NOT SHOWING")
        XCTAssertEqual(dashboard.pad.health, .bad)
        XCTAssertTrue(dashboard.pad.isBlank)
        XCTAssertFalse(dashboard.pad.isReady)
    }

    // MARK: - What the first viewport ends up with

    func testTheDashboardNeverShowsAGreenPadWithoutAHeartbeat() throws {
        let document = try status(Fixture.onlineStatus)
        var machine = LifecycleMachine()
        machine.observe(.status(document), at: now)
        let dashboard = DashboardBuilder.build(
            DashboardInput(status: document, machine: machine, now: now))
        XCTAssertEqual(dashboard.pad.health, .notReported)
        XCTAssertFalse(dashboard.pad.presence.isConnected)
        XCTAssertEqual(dashboard.pad.address, "https://crooks-mini.tail1234.ts.net/",
                       "the address is still shown — it is real, it is just not a connection")
    }
}
