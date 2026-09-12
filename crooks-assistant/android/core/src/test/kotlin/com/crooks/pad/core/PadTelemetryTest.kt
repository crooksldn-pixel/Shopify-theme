package com.crooks.pad.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PadTelemetryTest {

    private val captured = mutableListOf<PadEvent>()
    private fun telemetry() = PadTelemetry(sink = { captured += it })

    /**
     * THE TEST THIS FILE EXISTS FOR.
     *
     * `POST /telemetry` on the Mac keeps only fields whose names are in its own ALLOWED_FIELDS
     * set and DROPS the rest silently, answering 204 either way. So a pad can emit a perfectly
     * shaped event, receive a 204, and have the one field that explained the outage thrown
     * away at the door with nothing anywhere saying so. That is §26's lesson in its most
     * literal form — green because the wrong thing was measured — and this assertion is the
     * guard: if anybody adds a field the Mac will not keep, the build goes red HERE, where it
     * costs a minute, instead of in a timeline nobody can reconstruct six weeks later.
     *
     * The Mac's own file (app/routes/observe.py) is inside Phase 6's non-regression boundary
     * and cannot be changed to suit the pad. The pad bends to it.
     */
    @Test fun `every field of every pad event is one the Mac will actually keep`() {
        for ((kind, fields) in PadEventSpec.SPECS) {
            for (field in fields) {
                assertTrue(
                    "$kind declares field '$field', which POST /telemetry drops silently. " +
                        "Either rename it to one of ALLOWED_FIELDS in app/routes/observe.py, " +
                        "or accept that the value will never arrive.",
                    field in PadEventSpec.BACKEND_ALLOWED_FIELDS,
                )
            }
        }
    }

    /** The same endpoint drops any event whose kind does not match `^[a-z][a-z0-9_]{0,39}$`. */
    @Test fun `every pad event kind survives the Mac's kind pattern`() {
        val pattern = Regex("^[a-z][a-z0-9_]{0,39}$")
        for (kind in PadEventSpec.SPECS.keys) {
            assertTrue("$kind would be dropped by POST /telemetry", pattern.matches(kind))
            assertTrue("$kind should be namespaced pad_*", kind.startsWith("pad_"))
        }
    }

    @Test fun `§18's named events all exist`() {
        // The brief names them. If one is renamed, this says so rather than the event quietly
        // ceasing to be emitted.
        val required = listOf(
            "pad_app_started", "pad_foreground", "pad_background", "pad_webview_loaded",
            "pad_webview_error", "pad_network_changed", "pad_backend_reachable",
            "pad_backend_unreachable", "pad_mic_permission", "pad_renderer_crash",
            "pad_admin_entered", "pad_admin_exited", "pad_version",
        )
        for (kind in required) assertTrue("§18 requires $kind", PadEventSpec.allows(kind))
    }

    @Test fun `an undeclared field is dropped before it can reach the queue`() {
        // The PII defence is a whitelist, not a scrubber. A scrubber has to recognise the
        // thing it is protecting against; a whitelist does not have to recognise anything.
        val t = telemetry()
        val event = t.record(
            "pad_network_changed",
            mapOf("state" to "wifi", "reachable" to true, "ssid" to "GEORGE-BACK-OFFICE", "ip" to "100.64.1.7"),
            now = 1_000,
        )
        assertNotNull(event)
        assertTrue("state must survive", "state" in event!!.fields)
        assertFalse("an SSID names a place and must never leave the tablet", "ssid" in event.fields)
        assertFalse("an address identifies the tailnet node", "ip" in event.fields)
    }

    @Test fun `an unknown kind is rejected rather than emitted and lost`() {
        val t = telemetry()
        assertNull(t.record("pad_made_up", mapOf("state" to "x"), now = 1_000))
        assertEquals(1, t.rejected)
        assertEquals(0, t.emitted)
        assertTrue(captured.isEmpty())
    }

    @Test fun `there is no battery event to spam with`() {
        // §18: "meaningful transitions only — do NOT spam battery ticks". The strongest form
        // of that rule is that there is no kind for a battery tick, so nobody can reach for
        // one. Battery is a field of the device snapshot and nothing else.
        val t = telemetry()
        assertNull(t.record("pad_battery", mapOf("count" to 91), now = 0))
        assertNull(t.record("pad_battery_changed", mapOf("count" to 90), now = 0))
        for (kind in PadEventSpec.SPECS.keys) {
            assertFalse("$kind looks like a battery tick", kind.contains("battery"))
        }
    }

    @Test fun `a transition event repeats only when the transition is real`() {
        val t = telemetry()
        assertNotNull(t.record("pad_network_changed", mapOf("state" to "wifi"), now = 0))
        assertNull("the same network is not a change", t.record("pad_network_changed", mapOf("state" to "wifi"), now = 60_000))
        assertNotNull(t.record("pad_network_changed", mapOf("state" to "none"), now = 61_000))
        assertNotNull("and back again is a change", t.record("pad_network_changed", mapOf("state" to "wifi"), now = 62_000))
        assertEquals(3, t.emitted)
        assertEquals(1, t.suppressed)
    }

    @Test fun `an identical non-transition event is deduplicated for ten seconds`() {
        val t = telemetry()
        assertNotNull(t.record("pad_webview_error", mapOf("code" to "504"), now = 0))
        assertNull(t.record("pad_webview_error", mapOf("code" to "504"), now = 5_000))
        assertNotNull(t.record("pad_webview_error", mapOf("code" to "504"), now = 11_000))
        // A different value is a different event and is never suppressed.
        assertNotNull(t.record("pad_webview_error", mapOf("code" to "502"), now = 11_001))
    }

    @Test fun `every event carries a timestamp the Mac will keep`() {
        val t = telemetry()
        val event = t.record("pad_app_started", mapOf("name" to "CROOKS Pad"), now = 1_234)!!
        assertEquals(1_234L, event.fields["t"])
        assertTrue("t" in PadEventSpec.BACKEND_ALLOWED_FIELDS)
    }

    @Test fun `a long value is bounded here rather than trusted to be bounded there`() {
        val t = telemetry()
        val event = t.record("pad_webview_error", mapOf("reason" to "x".repeat(5_000)), now = 0)!!
        assertEquals(201, (event.fields["reason"] as String).length)
    }

    @Test fun `a url never enters an event with its path attached`() {
        // A CROOKS path can carry an order number or a message id. An origin cannot carry
        // anything, which is why originOnly exists and why the blocked-navigation event has no
        // field for an address at all.
        assertEquals(
            "https://crooks-assistant.taildfb357.ts.net",
            originOnly("https://crooks-assistant.taildfb357.ts.net/order/1934?email=george%40example.com"),
        )
        assertNull(originOnly("not a url"))
        assertFalse(
            "a blocked address is attacker-controlled text and has no field to arrive in",
            "url" in PadEventSpec.fieldsFor("pad_navigation_blocked"),
        )
    }

    @Test fun `the counters tell quiet apart from broken`() {
        val t = telemetry()
        t.record("pad_app_started", mapOf("name" to "a"), now = 0)
        t.record("pad_app_started", mapOf("name" to "a"), now = 1)
        t.record("pad_nonsense", emptyMap(), now = 2)
        assertEquals(1, t.emitted)
        assertEquals(1, t.suppressed)
        assertEquals(1, t.rejected)
    }
}
