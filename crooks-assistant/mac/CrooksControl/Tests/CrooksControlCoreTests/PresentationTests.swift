import XCTest
@testable import CrooksControlCore

/// SHOW ONLY WHAT MATTERS NOW — the rule, held to account.
///
/// The rejected build was rejected for what was ON it, not for how it was drawn: ten controls at
/// once, seven integrations as an admin table, a development Mac labelled DEGRADED. None of that
/// is a colour problem, and none of it could have been caught by looking at a screenshot. They
/// are all decisions, so they are all testable, and this is where they are tested.
final class PresentationTests: XCTestCase {

    let now = Date(timeIntervalSince1970: 1_789_000_000)

    func status(_ data: Data) throws -> StatusDocument {
        try Contract.decoder.decode(StatusDocument.self, from: data)
    }

    func actions() throws -> [ActionsDocument.Action] {
        try Contract.decoder.decode(ActionsDocument.self, from: Fixture.actions).actions
    }

    /// A dashboard built the way the app builds one, from real documents.
    func dashboard(_ data: Data, busy: String? = nil, plan: UpdateDocument? = nil,
                   outcome: UpdateDocument? = nil) throws -> (Dashboard, StatusDocument) {
        let document = try status(data)
        var machine = LifecycleMachine()
        machine.observe(.status(document), at: now)
        let built = DashboardBuilder.build(DashboardInput(
            status: document, actions: try actions(), machine: machine,
            plan: plan, outcome: outcome, busy: busy, now: now))
        return (built, document)
    }

    // MARK: - The three questions, and only those

    func testAHealthyApplianceIsQuietAndOffersOneThing() throws {
        let (board, document) = try dashboard(Fixture.onlineStatus)
        let screen = Presentation.screen(board, status: document, now: now)

        XCTAssertEqual(screen.word, "READY")
        XCTAssertEqual(screen.attention, .well)
        XCTAssertNil(screen.note, "nothing is wrong, so there is nothing to explain")
        XCTAssertEqual(screen.stages, [], "and nothing is in flight")

        // ONE action. The whole rejection in one assertion: START, STOP, RESTART, HEALTH, START
        // TEST, STOP TEST, OPEN REPORT, CHECK UPDATE, INSTALL UPDATE and ROLL BACK were all on
        // screen at once, so none of them was the answer to anything.
        XCTAssertEqual(screen.primary?.id, "session_start")
        XCTAssertEqual(screen.primary?.emphasis, .quiet,
                       "a calm screen does not need a loud button; nothing is wrong")
    }

    func testTheOwnerIsNeverShownMoreThanOneAction() throws {
        for fixture in [Fixture.onlineStatus, Fixture.offlineStatus, Fixture.degradedStatus,
                        Fixture.essentialDownStatus, Fixture.recordingStatus, Fixture.noRouteStatus] {
            let (board, document) = try dashboard(fixture)
            let screen = Presentation.screen(board, status: document, now: now)
            // `primary` is one optional, so this is true by construction — which is the point of
            // its being an optional and not an array. The assertion that matters is the second:
            // everything else is small text in the footer, not a control competing with it.
            XCTAssertLessThanOrEqual(screen.secondary.count, 3,
                                     "the footer is a way out, not a second control panel")
        }
    }

    // MARK: - §10. Expected absence is not failure

    func testADevelopmentMacIsReadyAndNamesItsEnvironment() throws {
        let raw = try XCTUnwrap(String(data: Fixture.onlineStatus, encoding: .utf8))
            .replacingOccurrences(of: "\"port\": 8000",
                                  with: "\"port\": 8000,\n  \"environment\": {\"name\": \"development\", "
                                      + "\"detail\": \"Fixture backend\", \"fixtures\": [\"gmail\", \"shopify\"]}")
        let document = try status(Data(raw.utf8))
        var machine = LifecycleMachine()
        machine.observe(.status(document), at: now)
        let board = DashboardBuilder.build(DashboardInput(status: document, actions: try actions(),
                                                          machine: machine, now: now))
        let screen = Presentation.screen(board, status: document, now: now)

        XCTAssertEqual(screen.word, "READY", "a correctly configured development Mac is not DEGRADED")
        XCTAssertEqual(screen.environment?.name, "DEVELOPMENT")
        XCTAssertEqual(screen.environment?.detail, "Fixture backend")
        XCTAssertEqual(screen.line, "Mac online · required systems healthy",
                       "and the sentence does not claim more than it knows")
    }

    func testARealMacSaysNothingAboutItsEnvironment() throws {
        let (board, document) = try dashboard(Fixture.onlineStatus)
        XCTAssertNil(Presentation.screen(board, status: document, now: now).environment,
                     "a chip on every screen forever is furniture, and furniture stops being read")
    }

    // MARK: - Failures are unmistakable, and their remedy is not painted as a danger

    func testAStoppedApplianceOffersExactlyOneThing() throws {
        let (board, document) = try dashboard(Fixture.offlineStatus)
        let screen = Presentation.screen(board, status: document, now: now)
        XCTAssertEqual(screen.word, "OFFLINE")
        XCTAssertEqual(screen.attention, .failure)
        XCTAssertEqual(screen.primary?.id, "start")
        XCTAssertEqual(screen.primary?.emphasis, .primary,
                       "bone, not red: the word above is already unmistakable, and painting the "
                           + "way out in the failure's colour makes the one thing that helps look "
                           + "like the one thing to avoid")
        XCTAssertNil(screen.pad, "the tablet is downstream of this and there is nothing to do about it")
    }

    func testARunningApplianceThatCannotWorkIsItsOwnState() throws {
        let (board, document) = try dashboard(Fixture.essentialDownStatus)
        let screen = Presentation.screen(board, status: document, now: now)
        XCTAssertEqual(screen.word, "NOT WORKING")
        XCTAssertEqual(screen.attention, .failure)
        XCTAssertNotNil(screen.note, "and it says WHAT is not working")
    }

    // MARK: - Invariant 12: no control is drawn that the script cannot perform

    func testNoButtonIsDrawnForAnActionTheScriptDoesNotOffer() throws {
        let (board, document) = try dashboard(Fixture.offlineStatus)
        // A script with no `start` action. The screen must lose the button, not draw a dead one.
        let stripped = Dashboard(
            lifecycle: board.lifecycle, headline: board.headline, explanation: board.explanation,
            accent: board.accent, services: board.services, pad: board.pad, session: board.session,
            identity: board.identity, groups: [], update: board.update, notice: board.notice,
            missingControls: ["START"], busy: nil, developer: nil)
        let screen = Presentation.screen(stripped, status: document, now: now)
        XCTAssertEqual(screen.word, "OFFLINE", "the state is still told truthfully")
        XCTAssertNil(screen.primary, "and no button is drawn for something the Mac cannot do")
    }

    func testTheBlankTabletGetsNoButtonBecauseThisMacCannotReloadIt() throws {
        // The state the old build could not express at all — and the temptation, having finally
        // been able to say it, is to put a RELOAD THE TABLET button under it. Nothing on this Mac
        // can reload the tablet's screen. The fix is on the tablet, in the owner's hand.
        let raw = try XCTUnwrap(String(data: Fixture.onlineStatus, encoding: .utf8))
            .replacingOccurrences(of: "\"port\": 8000",
                                  with: "\"port\": 8000,\n  \"pad\": {\"known\": true, \"alive\": true, "
                                      + "\"age_s\": 3.0, \"app\": \"CROOKS Pad 0.6.2\", \"version\": \"\", "
                                      + "\"build\": \"\", \"source\": \"pad\", \"detail\": \"last heard from 3s ago\", "
                                      + "\"showing_crooks\": false, \"webview\": \"crashed\"}")
        let document = try status(Data(raw.utf8))
        var machine = LifecycleMachine()
        machine.observe(.status(document), at: now)
        let board = DashboardBuilder.build(DashboardInput(status: document, actions: try actions(),
                                                          machine: machine, now: now))
        let screen = Presentation.screen(board, status: document, now: now)

        XCTAssertEqual(screen.word, "READY", "the MAC really is ready — that part was never wrong")
        XCTAssertEqual(screen.attention, .attention, "and the appliance is not calm")
        XCTAssertEqual(screen.pad?.word, "NOT SHOWING")
        XCTAssertNil(screen.primary, "no button that would do nothing")
        let note = try XCTUnwrap(screen.note)
        XCTAssertTrue(note.contains("Wake the tablet"), "the sentence carries him instead: \(note)")
    }

    // MARK: - A test running owns the window

    func testARunningTestShowsTheClockAndNothingElse() throws {
        let (board, document) = try dashboard(Fixture.recordingStatus)
        let screen = Presentation.screen(board, status: document, now: now)
        XCTAssertEqual(screen.eyebrow, "PHYSICAL TEST")
        XCTAssertEqual(screen.primary?.id, "session_stop")
        XCTAssertNil(screen.pad, "while a test runs, the tablet's row is not what is being read")
        XCTAssertEqual(screen.attention, .working)
    }

    func testAScriptTooOldToSendAStartTimeDoesNotDrawAClockReadingZero() throws {
        // 00:00 over a test that has been going an hour is worse than no clock at all.
        let (board, document) = try dashboard(Fixture.recordingStatus)
        guard document.testSession.startedAt == nil else {
            return XCTAssertEqual(Presentation.screen(board, status: document, now: now).wordIsFigure, true)
        }
        let screen = Presentation.screen(board, status: document, now: now)
        XCTAssertEqual(screen.word, "RECORDING")
        XCTAssertFalse(screen.wordIsFigure)
    }

    func testAFinishedTestLeadsWithWhatItFoundAndNotWithTheFactThatItFinished() throws {
        let (board, document) = try dashboard(Fixture.onlineStatus)
        let finished = FinishedTest(id: "s-4471", name: "Saturday counter", duration: 1_284,
                                    interactions: 47, issues: 3)
        let screen = Presentation.screen(board, status: document, finished: finished, now: now)
        XCTAssertEqual(screen.word, "TEST COMPLETE")
        XCTAssertEqual(screen.line, "3 owner issues recorded")
        XCTAssertEqual(screen.primary?.id, "report_open")
        XCTAssertEqual(screen.primary?.emphasis, .primary)
    }

    func testOneIssueIsNotCalledIssues() throws {
        let (board, document) = try dashboard(Fixture.onlineStatus)
        let finished = FinishedTest(id: "s", name: "n", duration: 60, interactions: 2, issues: 1)
        XCTAssertEqual(Presentation.screen(board, status: document, finished: finished, now: now).line,
                       "1 owner issue recorded")
    }

    // MARK: - An update on offer is an offer, not an alarm

    func testAnAvailableUpdateDoesNotLightAWarningLight() throws {
        let plan = try Contract.decoder.decode(UpdateDocument.self, from: Fixture.planAvailable)
        let (board, document) = try dashboard(Fixture.onlineStatus, plan: plan)
        let screen = Presentation.screen(board, status: document, now: now)
        XCTAssertEqual(screen.word, "UPDATE READY")
        XCTAssertEqual(screen.attention, .calm,
                       "nothing is wrong; an appliance that goes amber because a newer build "
                           + "exists has spent the colour it needs for the day something is")
        XCTAssertEqual(screen.primary?.id, "update")
    }

    func testAnUpdateThatMovedTheBuildAndDidNotComeBackOffersTheWayBack() throws {
        let outcome = try Contract.decoder.decode(UpdateDocument.self, from: Fixture.applyMovedButUnhealthy)
        let (board, document) = try dashboard(Fixture.onlineStatus, outcome: outcome)
        let screen = Presentation.screen(board, status: document, now: now)
        XCTAssertEqual(screen.word, "UPDATE FAILED")
        XCTAssertEqual(screen.attention, .failure)
        XCTAssertEqual(screen.primary?.id, "rollback")
        XCTAssertNil(screen.pad, "the tablet is not the subject")
    }

    // MARK: - Nothing reaches the screen with a credential on it

    func testEveryStringOnEveryScreenHasBeenThroughRedaction() throws {
        // §28, and it is not belt-and-braces: the sentences on these screens are built from the
        // control script's own output, and the stderr of a command handed a bad API key quotes it.
        for fixture in [Fixture.onlineStatus, Fixture.offlineStatus, Fixture.degradedStatus,
                        Fixture.essentialDownStatus, Fixture.recordingStatus] {
            let (board, document) = try dashboard(fixture)
            let screen = Presentation.screen(board, status: document, now: now)
            for text in [screen.word, screen.line, screen.note ?? "", screen.pad?.detail ?? ""] {
                XCTAssertEqual(text, Redaction.scrub(text),
                               "a string reached the screen that redaction would have changed: \(text)")
            }
        }
    }
}
