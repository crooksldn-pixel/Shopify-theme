import XCTest
@testable import CrooksControlCore

/// The small carries between the document and the button that have no cleverness in them and
/// would be discovered missing only on the Mac, where nothing here can run.
///
/// Every test in this file exists because the thing it checks is INVISIBLE when it breaks:
/// a button that runs in the wrong folder, a START that never says STARTING, a two-click
/// update that quietly became one click. None of them would fail a build; all of them would
/// fail in the shop.
final class WiringTests: XCTestCase {

    let now = Date(timeIntervalSince1970: 1_789_000_000)

    func dashboard(_ actions: [ActionsDocument.Action], status data: Data = Fixture.onlineStatus,
                   plan: UpdateDocument? = nil) throws -> Dashboard {
        let document = try Contract.decoder.decode(StatusDocument.self, from: data)
        var machine = LifecycleMachine()
        machine.observe(.status(document), at: now)
        return DashboardBuilder.build(DashboardInput(
            status: document, actions: actions, machine: machine, plan: plan, now: now))
    }

    func button(_ dashboard: Dashboard, _ id: String) -> ActionButton? {
        dashboard.groups.flatMap(\.buttons).first { $0.id == id }
    }

    // MARK: - Intent is read from the id, not from the kind

    func testStartSaysStartingWhicheverKindTheScriptGivesIt() throws {
        // START is kind "shell" today. If Workstream A makes it kind "control" instead — which
        // is a perfectly reasonable thing to do, since control.py would then own it — the app
        // must still enter STARTING when it is pressed. Deciding that from `kind` is how that
        // breaks silently.
        for kind in ["shell", "control", "something_new"] {
            let list = [ActionsDocument.Action(id: "start", label: "Start", kind: kind,
                                               group: "use", command: ["/usr/bin/true"])]
            let start = try XCTUnwrap(button(try dashboard(list, status: Fixture.offlineStatus), "start"))
            XCTAssertEqual(start.intent, .start, "kind \(kind) lost the intent")
        }
    }

    func testOnlyTheThreeLifecycleButtonsCarryAnIntent() {
        XCTAssertEqual(KnownAction.intent(for: "start"), .start)
        XCTAssertEqual(KnownAction.intent(for: "stop"), .stop)
        XCTAssertEqual(KnownAction.intent(for: "restart"), .restart)
        for id in ["open", "check", "update", "rollback", "logs", "tests", "session_start", ""] {
            XCTAssertNil(KnownAction.intent(for: id), "\(id) must not move the state machine")
        }
    }

    // MARK: - What a button needs to actually run

    func testTheFolderACommandExpectsToRunInIsCarriedThrough() throws {
        // Several of the scripts behind these buttons resolve paths against their working
        // directory. Dropping `cwd` on the way to the button loses that, and the failure is a
        // script complaining about a file it cannot find — nothing that points at this app.
        let actions = try Contract.decoder.decode(ActionsDocument.self, from: Fixture.actions).actions
        let dashboard = try dashboard(actions)
        let tests = try XCTUnwrap(button(dashboard, "tests"))
        XCTAssertEqual(tests.cwd, "/Users/george/crooks-assistant")
        XCTAssertEqual(tests.command?.first, "/Users/george/crooks-assistant/.venv/bin/pytest")
    }

    func testWhereToOpenAndWhatToRevealSurviveTheJourney() throws {
        let actions = try Contract.decoder.decode(ActionsDocument.self, from: Fixture.actions).actions
        let dashboard = try dashboard(actions)
        // The loopback address, not the Tailscale one, and that is the fixture being honest:
        // the actions document was captured on a machine with no Tailscale, while the status
        // fixtures were generated with a route stubbed in. The disagreement is real and worth
        // keeping — control.py bakes the address into the actions document when it is read,
        // and the app reads that document once. See Centre.refresh, which re-reads the actions
        // when the route changes, so a Tailscale that comes up later is not missed.
        XCTAssertEqual(button(dashboard, "open")?.url, "http://127.0.0.1:8000/")
        XCTAssertEqual(button(dashboard, "logs")?.path, "/Users/george/crooks-assistant/logs")
        XCTAssertNil(button(dashboard, "logs")?.command, "a folder is revealed, not executed")
    }

    func testAnOpenButtonWithNowhereToGoIsGrey() throws {
        let list = [
            ActionsDocument.Action(id: "open", label: "Open CROOKS Pad", kind: "open_url", group: "use"),
            ActionsDocument.Action(id: "logs", label: "Open logs", kind: "open_path", group: "look"),
        ]
        let dashboard = try dashboard(list)
        XCTAssertEqual(button(dashboard, "open")?.enabled, false)
        XCTAssertEqual(button(dashboard, "open")?.disabledReason,
                       "This button has no page to open, so there is nothing behind it.")
        XCTAssertEqual(button(dashboard, "logs")?.enabled, false)
    }

    // MARK: - The two-click update stays two clicks

    func testUpdateNeedsACheckEvenIfTheScriptStopsSayingSo() throws {
        // `needs_plan` is a flag in the document. If a future control.py stopped sending it,
        // a rule written as `if action.needsPlan && plan == nil` would turn UPDATE into a
        // one-click action that moves the build before the owner has seen either SHA.
        let list = [ActionsDocument.Action(id: "update", label: "Update", kind: "control",
                                           group: "update", command: ["/usr/bin/true"],
                                           confirm: true, confirmText: "Take it?",
                                           needsPlan: false)]
        let update = try XCTUnwrap(button(try dashboard(list), "update"))
        XCTAssertFalse(update.enabled)
        XCTAssertEqual(update.disabledReason,
                       "Press CHECK FOR UPDATE first, so you can see what would change.")

        let plan = try Contract.decoder.decode(UpdateDocument.self, from: Fixture.planAvailable)
        XCTAssertTrue(try XCTUnwrap(button(try dashboard(list, plan: plan), "update")).enabled)
    }

    // MARK: - Odd documents

    func testAButtonWithNoGroupGetsAHeadingRatherThanAnEmptyOne() throws {
        let list = [ActionsDocument.Action(id: "odd", label: "Odd", kind: "shell", group: "",
                                           command: ["/usr/bin/true"])]
        XCTAssertEqual(try dashboard(list).groups.first?.title, "Other")
    }

    func testAnActionWithNoCommandAtAllIsDrawnGreyRatherThanCrashingOrRunningNothing() throws {
        let list = [ActionsDocument.Action(id: "hollow", label: "Hollow", kind: "shell", group: "look")]
        let hollow = try XCTUnwrap(button(try dashboard(list), "hollow"))
        XCTAssertFalse(hollow.enabled)
        XCTAssertEqual(hollow.disabledReason, CommandGuard.Refusal.empty.sentence)
    }

    func testTheDashboardSurvivesAnActionsDocumentOfRubbish() throws {
        // Not a hypothetical: this is what a half-written control.py sends.
        let raw = Data(#"""
        {"contract": 1, "command": "actions", "ok": true,
         "actions": [{"id": "a"}, {"label": "no id"}, {"id": "c", "kind": 7, "group": ["x"]}]}
        """#.utf8)
        let document = try Contract.decoder.decode(ActionsDocument.self, from: raw)
        XCTAssertEqual(document.actions.count, 3)
        let dashboard = try dashboard(document.actions)
        XCTAssertEqual(dashboard.groups.count, 1, "all three fell into the one untitled group")
        XCTAssertTrue(dashboard.groups.allSatisfy { $0.buttons.allSatisfy { !$0.enabled } },
                      "none of them has a command, so none of them may be pressed")
    }
}
