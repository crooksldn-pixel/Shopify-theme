// THE DECISION LAYER, and it is the same one CrooksControlCore makes.
//
// Given the document `crooks-control status` really printed, plus whatever this app knows that
// the Mac does not (a test running, an update in flight), work out the ONE screen to draw:
// which word, which colour, which single action, and what — if anything — deserves the space
// between them.
//
// This file is the harness's copy of `Presentation.screen(...)` in Swift. It exists because the
// SwiftUI app cannot be compiled or drawn on this machine, and a design nobody has looked at is
// not a design. Keeping the decisions HERE rather than in the markup is the point: the harness
// renders the same judgements the product makes, so what is critiqued is the product.

// `solid` is the bone-filled button: the one unambiguous thing to press. It is deliberately not
// a colour — an appliance that is broken should not spend GREEN on its recovery button, and a
// finished test is not a success worth congratulating. Prominence and approval are different
// things and only one of them is wanted here.
export const TONE = { ok: "ok", warn: "warn", bad: "bad", quiet: "quiet", busy: "busy", solid: "solid" };

function mmss(seconds) {
  const s = Math.max(0, Math.round(seconds));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function ago(seconds) {
  if (seconds == null) return "";
  if (seconds < 10) return "just now";
  if (seconds < 90) return `${Math.round(seconds)}s ago`;
  if (seconds < 5400) return `${Math.round(seconds / 60)}m ago`;
  return `${(seconds / 3600).toFixed(1)}h ago`;
}

// WHAT IS ON THE TABLET — three facts, not one. `alive` is the transport, `webview` is the
// surface, `showing_crooks` is CROOKS itself. CONNECTED is a claim about the third.
function padLine(pad) {
  if (!pad || !pad.known) {
    return { word: "NOT REPORTED", tone: TONE.quiet, detail: "This Mac does not report the tablet's own check-in." };
  }
  const seen = ago(pad.age_s);
  if (pad.alive !== true) {
    const word = pad.age_s == null ? "NEVER CONNECTED" : "DISCONNECTED";
    return { word, tone: TONE.warn, detail: pad.age_s == null ? "The tablet has never used this address." : `Last seen ${seen}` };
  }
  if (pad.showing_crooks === false && (pad.webview === "error" || pad.webview === "crashed")) {
    return { word: "NOT SHOWING", tone: TONE.bad, detail: "The tablet is here and CROOKS is not on its screen." };
  }
  if (pad.showing_crooks === false) {
    return { word: "LOADING", tone: TONE.quiet, detail: "The screen is still coming up." };
  }
  return { word: "CONNECTED", tone: TONE.ok, detail: `Last seen ${seen}`, meta: pad.app || "" };
}

// The ids the control script really prints (`crooks-control actions`). Naming anything else
// here would draw a button the Mac cannot perform — invariant 12 — which is exactly what an
// earlier draft of this file did with a "reload the tablet" control that does not exist.
const OFFERED = new Set(["start", "stop", "open", "restart", "check", "update", "rollback",
                         "tests", "tests_ui", "session_start", "session_status", "session_stop",
                         "report", "report_open", "logs", "folder"]);
const ACT = (id, label, tone = TONE.quiet) => (OFFERED.has(id) ? { id, label, tone } : null);
const some = (...actions) => actions.filter(Boolean);

// System Details is a disclosure in the app, not a command, so it is the one entry that does
// not have to be in the actions document.
const DETAILS = { id: "details", label: "System Details", tone: TONE.quiet };

export function screen(state) {
  const doc = state.status || {};
  const app = state.app || {};
  const pad = padLine(doc.pad);
  const env = doc.environment && doc.environment.name
    ? { name: doc.environment.name.toUpperCase(), detail: doc.environment.detail } : null;
  const build = (doc.build && doc.build.current) || {};
  const foot = {
    version: (doc.lifecycle && doc.lifecycle.version) || build.version || "0.6.2",
    build: build.short || "",
  };

  const base = { pad, env, foot, more: [] };

  // ---- an update in flight owns the screen. Nothing else is worth reading while it runs.
  if (app.update && app.update.state === "running") {
    return { ...base, word: "UPDATING", tone: TONE.busy, line: `CROOKS OS ${app.update.version}`,
             pad: null, stages: app.update.stages, primary: null, quiet: true };
  }
  if (app.update && app.update.state === "failed") {
    return { ...base, word: "UPDATE FAILED", tone: TONE.bad,
             line: `Previous build restored · ${app.update.restored.slice(0, 8)}`,
             note: app.update.why,
             pad: null,
             primary: ACT("rollback", "ROLL BACK", TONE.solid),
             more: some(ACT("logs", "Open logs"), DETAILS) };
  }

  // ---- a test running owns it too, for the same reason.
  if (app.test && app.test.active) {
    // THE TIMER IS THE HERO, not the words "physical test". While a test is running, what the
    // owner wants off this screen at a glance is how long it has been going and whether the
    // tablet is still with him; the mode is context, so it goes above in small caps and the
    // clock takes the size. Two large elements competing was the first draft's mistake.
    return { ...base, eyebrow: "PHYSICAL TEST", word: mmss(app.test.elapsed_s), tone: TONE.busy,
             mono: true,
             line: [app.test.name, `${app.test.interactions} interactions`,
                    pad.word === "CONNECTED" ? "Pad connected" : pad.word.toLowerCase()].join(" · "),
             pad: null,
             primary: ACT("session_stop", "STOP & ANALYSE", TONE.warn),
             more: [DETAILS] };
  }
  if (app.report) {
    const n = app.report.issues;
    return { ...base, word: "TEST COMPLETE", tone: TONE.quiet,
             line: `${n} owner ${n === 1 ? "issue" : "issues"} recorded`,
             note: `${app.report.name} · ${mmss(app.report.duration_s)} · ${app.report.interactions} interactions`,
             primary: ACT("report_open", "OPEN REPORT", TONE.solid),
             more: some(ACT("session_start", "Run another test"), DETAILS) };
  }

  // ---- the Mac itself. Stopped and broken come before anything optional.
  if (doc.state === "RED" && (doc.issues || []).includes("the assistant is not answering")) {
    return { ...base, word: "OFFLINE", tone: TONE.bad, line: "CROOKS OS is not running on this Mac.",
             pad: null,
             primary: ACT("start", "START CROOKS OS", TONE.solid),
             more: [DETAILS] };
  }
  if (doc.state === "RED") {
    const down = doc.issues || [];
    return { ...base, word: "NOT WORKING", tone: TONE.bad,
             line: `CROOKS OS is running and cannot do its job.`,
             note: doc.why,
             // The tablet is downstream of this and there is nothing to do about it here.
             pad: null,
             // Bone, not red. The word and the sentence above are already unmistakable; painting
             // the remedy in the failure's colour makes the one thing that helps look like the
             // one thing to avoid.
             primary: ACT("restart", "RESTART CROOKS OS", TONE.solid),
             more: some(ACT("logs", "Open logs"), DETAILS) };
  }

  // ---- an update on offer is not an alarm, so it sits under a working appliance.
  if (app.update && app.update.state === "available") {
    // Quiet, not amber. Nothing is wrong — a newer build existing is an offer, and an appliance
    // that lights a warning light because an update is available has spent the colour it needs
    // for the day something is actually the matter.
    return { ...base, word: "UPDATE READY", tone: TONE.quiet,
             line: `CROOKS OS ${app.update.version} · ${app.update.behind} changes`,
             primary: ACT("update", "INSTALL UPDATE", TONE.solid),
             more: some(ACT("session_start", "Start physical test"), DETAILS) };
  }

  // ---- working. The tablet decides what the one action should be.
  const line = env ? "Mac online · required systems healthy" : "Mac online · all systems healthy";
  if (pad.tone === TONE.bad) {
    return { ...base, word: "READY", tone: TONE.warn,
             line: env ? "Mac online · CROOKS OS healthy" : "Mac online · CROOKS OS healthy",
             // NO BUTTON. Nothing on this Mac can reload the tablet's screen — the fix is on the
             // tablet, in the owner's hand — so the sentence carries him instead of a control
             // that would do nothing.
             note: "CROOKS OS is well. The tablet is on and not showing CROOKS. "
                 + "Wake the tablet and let CROOKS Pad load again.",
             primary: null,
             more: some(ACT("session_start", "Start physical test"), DETAILS) };
  }
  if (pad.tone === TONE.warn) {
    return { ...base, word: "READY", tone: TONE.ok, line,
             primary: ACT("session_start", "START PHYSICAL TEST", TONE.quiet),
             more: some(ACT("restart", "Restart CROOKS OS"), DETAILS) };
  }
  // Neutral, not green. Nothing is wrong, so nothing needs a colour: a green button on a calm
  // screen is the appliance congratulating itself, and it spends the one colour that should
  // mean something when it finally appears.
  return { ...base, word: "READY", tone: TONE.ok, line,
           primary: ACT("session_start", "START PHYSICAL TEST", TONE.quiet),
           more: some(ACT("restart", "Restart CROOKS OS"), DETAILS) };
}
