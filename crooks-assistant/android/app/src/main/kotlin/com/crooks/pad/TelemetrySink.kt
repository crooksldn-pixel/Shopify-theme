package com.crooks.pad

import com.crooks.pad.core.PadEvent
import org.json.JSONArray
import org.json.JSONObject

/**
 * CROOKS Pad — where a pad_* event goes.
 *
 * Two destinations, and the second one is conditional in a way worth being explicit about.
 *
 * 1. A LOCAL RING BUFFER, always. Two hundred events, in memory, shown on the diagnostics
 *    screen newest-first. This is the destination that works when the Mac is off — which is
 *    precisely when somebody is looking at diagnostics — and it is why the pad's account of
 *    itself does not depend on the thing it is complaining about being reachable.
 *
 * 2. `POST /telemetry` ON THE MAC, only while a test session is running. That is not a choice
 *    this workstream made: the endpoint drops everything with a 204 unless
 *    `runtime.timeline.active` is set, and `app/routes/observe.py` is inside Phase 6's
 *    non-regression boundary. So the pad learns the session id from `/health` — the same
 *    field, `observability.test_session`, that web/telemetry.js reads — and posts only when
 *    there is one. Outside a session, pad telemetry exists locally and nowhere else, and the
 *    diagnostics screen says so rather than implying that events are being collected.
 *
 * The batch shape is `{session_id, events:[...]}`, matching what the endpoint parses. Events
 * arrive already shaped by [com.crooks.pad.core.PadTelemetry], which has dropped any field the
 * Mac would have discarded — see the note at the top of that file for why that matters.
 */
class TelemetrySink(private val probe: BackendProbe) {

    private val ring = ArrayDeque<String>(RING_SIZE)
    private val pending = ArrayList<PadEvent>(FLUSH_AT)

    /** The Mac's active test session, learned from `/health`. Null means nothing is collecting. */
    @Volatile var testSessionId: String? = null

    @Synchronized
    fun accept(event: PadEvent) {
        ring.addLast(render(event))
        while (ring.size > RING_SIZE) ring.removeFirst()

        if (testSessionId == null) return
        pending += event
        if (pending.size >= FLUSH_AT) flush()
    }

    /** Called on the state timer and when the app goes to the background. */
    @Synchronized
    fun flush() {
        val session = testSessionId ?: return
        if (pending.isEmpty()) return
        val events = JSONArray()
        for (event in pending) {
            val json = JSONObject()
            json.put("kind", event.kind)
            for ((key, value) in event.fields) json.put(key, value)
            events.put(json)
        }
        pending.clear()
        val body = JSONObject().put("session_id", session).put("events", events).toString()
        probe.post("/telemetry", body)
    }

    @Synchronized
    fun recent(limit: Int = 40): List<String> = ring.toList().takeLast(limit).asReversed()

    private fun render(event: PadEvent): String {
        val fields = event.fields.entries
            .filter { it.key != "t" }
            .joinToString(" ") { "${it.key}=${it.value}" }
        val at = event.fields["t"] as? Long ?: 0L
        return "$at ${event.kind} $fields".trimEnd()
    }

    private companion object {
        const val RING_SIZE = 200
        const val FLUSH_AT = 20
    }
}
