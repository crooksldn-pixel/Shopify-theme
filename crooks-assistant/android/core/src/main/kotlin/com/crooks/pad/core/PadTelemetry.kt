package com.crooks.pad.core

/**
 * CROOKS Pad — §18, the appliance's own account of itself.
 *
 * THE THING THAT MAKES THIS FILE UNUSUAL, AND THE REASON IT IS WORTH READING. The pad does not
 * own the endpoint it posts to. `POST /telemetry` lives on the Mac, in
 * `app/routes/observe.py`, and that file is inside Phase 6's non-regression boundary — it may
 * not be changed by this workstream. It does two things that a naive native client would walk
 * straight into:
 *
 *   1. It requires the event's `kind` to match `^[a-z][a-z0-9_]{0,39}$`. An event that does
 *      not is DROPPED ENTIRELY, silently, with a 204 on the wire exactly as if it had been
 *      accepted.
 *   2. It keeps only fields whose names are in its own `ALLOWED_FIELDS` set. A field outside
 *      that set is DROPPED, silently, and the event around it is still stored — so the event
 *      arrives looking healthy with the one interesting value missing.
 *
 * That is §26's lesson wearing its most literal costume: a pad that "emits telemetry
 * successfully" while the field that would have explained the outage was thrown away at the
 * door, and a 204 to say so. [BACKEND_ALLOWED_FIELDS] below is therefore a copy of the Mac's
 * vocabulary, and [PadTelemetryTest] asserts that every field of every event this shell can
 * emit is in it. If someone adds `pad_wifi_ssid` with a field called `ssid`, the build goes
 * red here rather than the value going quietly missing in production.
 *
 * PII (§18, invariant 10). The defence is not a scrubber that looks for things that resemble
 * secrets — that is a filter that fails the first time something new resembles nothing. It is
 * a whitelist: each event kind declares the fields it may carry, [record] builds the outgoing
 * map from that declaration and nothing else, and an undeclared key is dropped before it can
 * reach a queue. Specifically never present anywhere in this file: Wi-Fi SSID or BSSID, IP
 * address, MAC address, device serial, any account or e-mail address, any URL path or query,
 * and any text the owner said or the Mac answered. A URL that does reach an event is reduced
 * to its origin by [originOnly] first.
 *
 * NOT SPAMMING (§18, "meaningful transitions only"). Two mechanisms, because they catch
 * different things. Transition events — network, backend reachability, foreground — carry a
 * key and are dropped when the key has not changed. Everything else is dropped when an
 * identical event was emitted within [DEDUPE_WINDOW_MS]. Battery gets neither, because
 * battery is not an event at all: it is a field of the snapshot that rides along with
 * `pad_app_started` and `pad_foreground`, and there is deliberately no `pad_battery` kind for
 * anyone to reach for.
 */

data class PadEvent(val kind: String, val fields: Map<String, Any?>)

/** What the shell may emit, and what each kind may say. Nothing outside this reaches the Mac. */
object PadEventSpec {

    /**
     * A copy, by hand, of `ALLOWED_FIELDS` in crooks-assistant/app/routes/observe.py.
     *
     * Only the subset the pad uses is listed: the Mac's set is larger and full of fields that
     * belong to the web layer's own vocabulary. Copying only what is used means this list can
     * be read as "what a pad event says" rather than as a mirror to be kept in sync wholesale.
     */
    val BACKEND_ALLOWED_FIELDS: Set<String> = setOf(
        "kind", "t", "session_id", "state", "code", "reason", "detail", "name", "mode", "via",
        "status", "ms", "elapsed_ms", "count", "reachable", "offline", "seq", "error_kind",
        "phase", "outcome", "label", "action", "target", "id", "from", "to", "message",
    )

    val SPECS: Map<String, Set<String>> = mapOf(
        // Once per process. Carries the device snapshot's non-identifying parts so that every
        // later event can be read against a known tablet without repeating itself.
        "pad_app_started" to setOf("name", "detail", "mode", "count", "state"),
        // Lifecycle. `state` is "foreground"/"background"; `elapsed_ms` is how long the other
        // way round lasted, which is what tells a screen-off from a genuine backgrounding.
        "pad_foreground" to setOf("state", "elapsed_ms"),
        "pad_background" to setOf("state", "elapsed_ms"),
        // The workspace arrived. `mode` is "confirmed" or "assumed" — see ConnectionMachine;
        // this is the field that says which measurement was actually taken.
        "pad_webview_loaded" to setOf("mode", "ms", "state"),
        "pad_webview_error" to setOf("code", "reason", "error_kind", "state"),
        // A navigation the shell refused. `reason` names the rule; there is deliberately no
        // field for the address, because a blocked address is attacker-controlled text.
        "pad_navigation_blocked" to setOf("reason", "target"),
        "pad_network_changed" to setOf("state", "reachable", "offline"),
        "pad_backend_reachable" to setOf("state", "ms", "detail"),
        "pad_backend_unreachable" to setOf("state", "reason", "count"),
        "pad_mic_permission" to setOf("outcome", "reason", "state"),
        "pad_renderer_crash" to setOf("reason", "count", "state"),
        "pad_admin_entered" to setOf("via"),
        "pad_admin_exited" to setOf("via", "elapsed_ms", "action"),
        "pad_version" to setOf("name", "detail", "mode"),
        "pad_state_changed" to setOf("from", "to", "reason", "count"),
        "pad_kiosk_stage" to setOf("mode", "detail"),
    )

    fun allows(kind: String): Boolean = kind in SPECS

    fun fieldsFor(kind: String): Set<String> = SPECS[kind].orEmpty()
}

/**
 * Reduces any URL to its origin. Used before a URL-shaped value may go into an event at all.
 * A CROOKS path can carry an order number or a message id; an origin cannot carry anything.
 */
fun originOnly(url: String?): String? = UrlParser.origin(url)?.toString()

class PadTelemetry(
    private val sink: (PadEvent) -> Unit,
    private val dedupeWindowMs: Long = DEDUPE_WINDOW_MS,
) {

    companion object {
        const val DEDUPE_WINDOW_MS: Long = 10_000

        /** Kinds whose point is the transition, not the value. */
        private val TRANSITION_KINDS = setOf(
            "pad_network_changed", "pad_backend_reachable", "pad_backend_unreachable",
            "pad_foreground", "pad_background", "pad_state_changed",
        )
    }

    private val lastTransitionKey = HashMap<String, String>()
    private val lastEmittedAt = HashMap<String, Long>()

    var emitted: Int = 0
        private set
    var suppressed: Int = 0
        private set
    var rejected: Int = 0
        private set

    /**
     * Shape, filter and possibly emit. Returns the event that went to the sink, or null when
     * nothing did — and the three counters say which of the three reasons applied, so that
     * "telemetry is quiet" can be told apart from "telemetry is broken" in diagnostics.
     */
    fun record(kind: String, fields: Map<String, Any?> = emptyMap(), now: Long): PadEvent? {
        if (!PadEventSpec.allows(kind)) { rejected++; return null }
        val allowed = PadEventSpec.fieldsFor(kind)
        val shaped = LinkedHashMap<String, Any?>()
        for ((key, value) in fields) {
            if (key !in allowed) continue
            if (value == null) continue
            shaped[key] = bound(value)
        }

        if (kind in TRANSITION_KINDS) {
            val key = shaped.entries.joinToString("|") { "${it.key}=${it.value}" }
            if (lastTransitionKey[kind] == key) { suppressed++; return null }
            lastTransitionKey[kind] = key
        } else {
            val key = kind + "|" + shaped.entries.joinToString("|") { "${it.key}=${it.value}" }
            val last = lastEmittedAt[key]
            if (last != null && now - last < dedupeWindowMs) { suppressed++; return null }
            lastEmittedAt[key] = now
        }

        val event = PadEvent(kind, shaped + mapOf("t" to now))
        emitted++
        sink(event)
        return event
    }

    /**
     * Values are bounded here rather than trusted. The Mac bounds them too, at 2000
     * characters, but a shell that sends a megabyte and relies on the far end to trim it is a
     * shell that will one day be pointed at something that does not trim.
     */
    private fun bound(value: Any): Any = when (value) {
        is String -> if (value.length > 200) value.take(200) + "…" else value
        is Boolean, is Int, is Long, is Double, is Float -> value
        is Enum<*> -> value.name.lowercase()
        else -> value.toString().take(200)
    }
}
