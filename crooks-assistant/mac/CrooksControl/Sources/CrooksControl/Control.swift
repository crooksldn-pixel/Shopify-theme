import Foundation

// Where the checkout is, how this script is run, and how its output becomes a document.
//
// Everything this app does to the Mac goes through one command: the project's own
// scripts/control.py, run by the project's own .venv. That is the whole of the app's
// authority — it knows the name of that script and nothing else about how CROOKS OS works.

enum Checkout {
    static let key = "crooks.projectFolder"

    /// The folder the owner picked, if it still looks like the project; otherwise the first
    /// of the usual places that does. `nil` means: ask him.
    static func resolve() -> URL? {
        if let saved = UserDefaults.standard.string(forKey: key) {
            let url = URL(fileURLWithPath: saved, isDirectory: true)
            if looksRight(url) { return url }
        }
        let home = FileManager.default.homeDirectoryForCurrentUser
        let candidates = [
            "crooks-assistant",
            "Shopify-theme/crooks-assistant",
            "Documents/crooks-assistant",
            "Developer/crooks-assistant",
            "code/crooks-assistant"
        ].map { home.appendingPathComponent($0, isDirectory: true) }
        return candidates.first(where: looksRight)
    }

    static func looksRight(_ url: URL) -> Bool {
        FileManager.default.fileExists(atPath: url.appendingPathComponent("scripts/control.py").path)
    }

    static func remember(_ url: URL) {
        UserDefaults.standard.set(url.path, forKey: key)
    }
}

enum ControlError: LocalizedError {
    case noCheckout
    case noPython(String)
    case failed(String)
    case badContract(Int)

    var errorDescription: String? {
        switch self {
        case .noCheckout:
            return "I cannot find the CROOKS OS folder. Choose it below — it is the one holding scripts/control.py."
        case .noPython(let path):
            return "There is no Python at \(path). Run `make venv` in the project folder once."
        case .failed(let text):
            return text
        case .badContract(let version):
            return "The project's crooks-control speaks version \(version); this app reads \(Contract.expected). Build the app again from this checkout."
        }
    }
}

/// One run of `crooks-control <subcommand>`, decoded.
struct Control {
    let root: URL

    var python: URL { root.appendingPathComponent(".venv/bin/python") }
    var script: URL { root.appendingPathComponent("scripts/control.py") }

    static func here() throws -> Control {
        guard let root = Checkout.resolve() else { throw ControlError.noCheckout }
        return Control(root: root)
    }

    func status() async throws -> StatusDocument {
        let document: StatusDocument = try await document(["status"])
        guard document.contract == Contract.expected else { throw ControlError.badContract(document.contract) }
        return document
    }

    func actions() async throws -> ActionsDocument {
        try await document(["actions"])
    }

    /// "Check for update": fetches, and changes nothing.
    func plan() async throws -> UpdateDocument {
        try await document(["plan"])
    }

    /// The click. Fast-forward only, the suite, the restart, the health read, the tablet's
    /// address, and the mark — all of it on the script's side.
    func apply() async throws -> UpdateDocument {
        try await document(["apply", "--yes"])
    }

    func rollback() async throws -> UpdateDocument {
        try await document(["rollback", "--yes"])
    }

    private func document<T: Decodable>(_ arguments: [String]) async throws -> T {
        let data = try await run(arguments)
        do {
            return try Contract.decoder.decode(T.self, from: data)
        } catch {
            let text = String(data: data, encoding: .utf8) ?? ""
            throw ControlError.failed("crooks-control \(arguments.joined(separator: " ")) answered something I could not read.\n\n\(text.prefix(400))")
        }
    }

    /// The subprocess. stdout is one JSON document; a non-zero exit is not an error here,
    /// because the document itself says what went wrong and is worth showing.
    private func run(_ arguments: [String]) async throws -> Data {
        guard FileManager.default.isExecutableFile(atPath: python.path) else {
            throw ControlError.noPython(python.path)
        }
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async {
                let task = Process()
                task.executableURL = python
                task.arguments = [script.path] + arguments
                task.currentDirectoryURL = root
                let out = Pipe(), err = Pipe()
                task.standardOutput = out
                task.standardError = err
                do {
                    try task.run()
                } catch {
                    continuation.resume(throwing: ControlError.failed("I could not run \(python.path): \(error.localizedDescription)"))
                    return
                }
                let data = out.fileHandleForReading.readDataToEndOfFile()
                let problem = String(data: err.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                task.waitUntilExit()
                if data.isEmpty {
                    continuation.resume(throwing: ControlError.failed(problem.isEmpty ? "crooks-control said nothing at all." : problem))
                } else {
                    continuation.resume(returning: data)
                }
            }
        }
    }
}

/// A button of kind "shell" or "control" whose output the owner watches: the suite, the UI
/// run, a report. Lines arrive as they are printed.
@MainActor
final class CommandLog: ObservableObject {
    @Published var title: String = ""
    @Published var lines: [String] = []
    @Published var running = false
    @Published var finished: Int32? = nil

    private var task: Process?

    func start(_ action: ActionsDocument.Action) {
        guard let argv = action.command, let first = argv.first else { return }
        stop()
        title = action.label
        lines = []
        finished = nil
        running = true
        let process = Process()
        process.executableURL = URL(fileURLWithPath: first)
        process.arguments = Array(argv.dropFirst())
        if let cwd = action.cwd { process.currentDirectoryURL = URL(fileURLWithPath: cwd, isDirectory: true) }
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let chunk = handle.availableData
            guard !chunk.isEmpty, let text = String(data: chunk, encoding: .utf8) else { return }
            Task { @MainActor [weak self] in
                self?.append(text)
            }
        }
        process.terminationHandler = { [weak self] finishedProcess in
            Task { @MainActor [weak self] in
                self?.running = false
                self?.finished = finishedProcess.terminationStatus
                pipe.fileHandleForReading.readabilityHandler = nil
            }
        }
        do {
            try process.run()
            task = process
        } catch {
            running = false
            lines = ["I could not run \(first): \(error.localizedDescription)"]
        }
    }

    func stop() {
        if let task, task.isRunning { task.terminate() }
        task = nil
        running = false
    }

    private func append(_ text: String) {
        for line in text.split(separator: "\n", omittingEmptySubsequences: false) where !line.isEmpty {
            lines.append(String(line))
        }
        // An hour of output is not something anyone reads; the last thousand lines are.
        if lines.count > 1000 { lines.removeFirst(lines.count - 1000) }
    }
}
