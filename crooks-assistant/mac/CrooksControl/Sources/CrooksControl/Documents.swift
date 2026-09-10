import Foundation

// The documents scripts/control.py prints, and nothing more. Every field here is named in
// `crooks-control contract`, and tests/test_control.py fails if the two ever part company.
//
// One decoder for all of them: the Python side writes snake_case, this side reads camelCase.

enum Contract {
    /// The document version this build of the app understands. A newer script is refused with
    /// one line rather than drawn with fields that have moved.
    static let expected = 1

    static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()
}

/// The one colour. RED beats BLUE beats AMBER beats GREEN — decided on the Python side; this
/// is only how each one is drawn.
enum Overall: String, Decodable {
    case green = "GREEN"
    case blue = "BLUE"
    case amber = "AMBER"
    case red = "RED"

    /// The dot in the menu bar. An SF Symbol, so it reads at menu-bar size and in both
    /// appearances; the colour it is drawn in is in Views.swift, where AppKit is.
    var symbol: String {
        switch self {
        case .green: return "checkmark.circle.fill"
        case .blue: return "record.circle.fill"
        case .amber: return "exclamationmark.circle.fill"
        case .red: return "xmark.circle.fill"
        }
    }
}

struct StatusDocument: Decodable {
    let contract: Int
    let command: String
    let ok: Bool
    let at: Double
    let state: Overall
    let headline: String
    let why: String
    let issues: [String]
    let degraded: [String]
    let rows: [Row]
    let build: BuildIdentifiers
    let tablet: Tablet
    let mutation: Mutation
    let testSession: TestSession
    let localWork: LocalWork
    let rollback: Rollback
    let port: Int

    struct Row: Decodable, Identifiable {
        let key: String
        let label: String
        let state: String       // "ok" | "off" | "bad"
        let value: String
        let detail: String

        var id: String { key }
    }

    struct Tablet: Decodable {
        let host: String
        let url: String
        let note: String
        let local: String
    }

    struct Mutation: Decodable {
        let state: String
        let detail: String
    }

    struct TestSession: Decodable {
        let active: Bool
        let id: String
        let name: String
    }
}

struct BuildIdentifiers: Decodable {
    let current: Build?
    let candidate: Build?
    let lastKnownGood: Build?
    let was: Build?

    struct Build: Decodable {
        let sha: String?
        let short: String?
        let branch: String?
        let detached: Bool?
        let subject: String?
        let build: String?
        let recordedAt: Double?
    }
}

struct LocalWork: Decodable {
    let dirty: [String]
    let blocking: [String]
    let stops: Bool
}

struct Rollback: Decodable {
    let available: Bool
    let safe: Bool
    let sha: String
    let short: String
    let reason: String
    let note: String
}

struct Stop: Decodable {
    let stage: String
    let reason: String
}

struct Stage: Decodable, Identifiable {
    let stage: String
    let state: String       // "ok" | "skip" | "fail" | "warn"
    let detail: String

    var id: String { stage + detail }
}

/// `plan` and `apply` are one shape to this side: the update document, what it did, and what
/// to do next. Which fields are filled depends on how far it got, so most are optional.
struct UpdateDocument: Decodable {
    let contract: Int
    let command: String
    let ok: Bool
    let update: Update?
    let build: BuildIdentifiers?
    let localWork: LocalWork?
    let rollback: Rollback?
    let stages: [Stage]?
    let markedGood: Marked?
    let stop: Stop?
    let next: String?
    let click: Click?

    struct Update: Decodable {
        let branch: String
        let behind: Int
        let ahead: Int
        let fastForward: Bool
        let deps: [String]
        let changedFiles: Int
        let moved: Bool
        let tested: Bool
        let restarted: Bool
        let verified: Bool
        let stages: [Stage]
        let stop: Stop?
        let current: BuildIdentifiers.Build?
        let candidate: BuildIdentifiers.Build?
    }

    struct Marked: Decodable {
        let short: String
        let build: String
    }

    struct Click: Decodable {
        let label: String
        let enabled: Bool
    }
}

struct ActionsDocument: Decodable {
    let contract: Int
    let actions: [Action]

    struct Action: Decodable, Identifiable {
        let id: String
        let label: String
        let kind: String            // "shell" | "control" | "open_url" | "open_path"
        let group: String           // "use" | "update" | "test" | "look"
        let command: [String]?
        let cwd: String?
        let url: String?
        let path: String?
        let confirm: Bool
        let confirmText: String?
        let why: String
    }
}
