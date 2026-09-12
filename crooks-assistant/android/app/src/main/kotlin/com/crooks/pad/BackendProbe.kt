package com.crooks.pad

import com.crooks.pad.core.ProbeFailure
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import javax.net.ssl.HttpsURLConnection

/**
 * CROOKS Pad — "is the Mac there", asked cheaply and answered honestly.
 *
 * The endpoint is `/ping` on the Mac, which exists for exactly this: no external call, no
 * cache, a few hundred bytes, and it carries `uptime_s`, which is what lets the pad tell a Mac
 * that has just been switched on from a Mac that is broken. `/health` is NOT used for this —
 * it runs a real Shopify query, a Gmail profile fetch and half a second of Whisper inference,
 * and polling it every few seconds would put a permanent hum on the Mac and on the Shopify
 * rate budget for the sake of a question `/ping` answers for free.
 *
 * WHAT "ANSWERED" MEANS HERE, because this is where a probe usually lies. A 200 is not
 * sufficient: a captive portal, a misrouted reverse proxy and a Tailscale node answering for
 * the wrong service all return 200 with something that is not CROOKS. So the probe requires a
 * 200 AND a JSON body AND `ok: true` in it. Anything else — a 200 of HTML, a redirect to a
 * login page, a 503 from a proxy — is BAD_ANSWER, which the state machine reads as "the Mac
 * is up, CROOKS is not serving", and which is a materially different sentence from "the Mac
 * is off".
 *
 * No HTTP library. `HttpsURLConnection` is in the platform, the request is one GET with two
 * timeouts, and an appliance shell with a dependency graph is an appliance shell that fails
 * to build one day for a reason nobody in the shop can fix.
 */
class BackendProbe(private val origin: String) {

    data class Success(val build: String, val uptimeSeconds: Double, val elapsedMs: Long)
    data class Failure(val failure: ProbeFailure, val detail: String, val elapsedMs: Long)

    sealed interface Result {
        data class Ok(val success: Success) : Result
        data class Bad(val failure: Failure) : Result
    }

    private val executor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "crooks-pad-probe").apply { isDaemon = true }
    }

    /** Runs off the main thread; [onResult] is posted back by the caller's handler. */
    fun probe(onResult: (Result) -> Unit) {
        executor.execute {
            val result = runCatching { probeBlocking() }.getOrElse { throwable ->
                Result.Bad(Failure(ProbeFailure.UNREACHABLE, throwable.javaClass.simpleName, 0))
            }
            onResult(result)
        }
    }

    /** A one-off GET for the small extras: the test-session id from `/health`. Best-effort. */
    fun get(path: String, onResult: (JSONObject?) -> Unit) {
        executor.execute {
            val body = runCatching { readJson(path, HEALTH_TIMEOUT_MS) }.getOrNull()
            onResult(body)
        }
    }

    fun post(path: String, body: String) {
        executor.execute {
            runCatching {
                val connection = open(path, PROBE_TIMEOUT_MS)
                connection.requestMethod = "POST"
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                connection.responseCode
                connection.disconnect()
            }
            // Deliberately swallowed. Telemetry is an account of what happened, not a thing
            // the pad waits on or reacts to; a shell that retried its own telemetry would
            // spend an outage talking about the outage.
        }
    }

    fun shutdown() {
        executor.shutdownNow()
    }

    private fun probeBlocking(): Result {
        val started = System.currentTimeMillis()
        val connection = open("/ping", PROBE_TIMEOUT_MS)
        try {
            val status = connection.responseCode
            val elapsed = System.currentTimeMillis() - started
            if (status != HttpURLConnection.HTTP_OK) {
                return Result.Bad(Failure(ProbeFailure.BAD_ANSWER, "http_$status", elapsed))
            }
            val text = connection.inputStream.bufferedReader().use { it.readText() }
            val json = runCatching { JSONObject(text) }.getOrNull()
                ?: return Result.Bad(Failure(ProbeFailure.BAD_ANSWER, "not_json", elapsed))
            if (!json.optBoolean("ok", false)) {
                return Result.Bad(Failure(ProbeFailure.BAD_ANSWER, "not_ok", elapsed))
            }
            return Result.Ok(
                Success(
                    build = json.optString("build", ""),
                    uptimeSeconds = json.optDouble("uptime_s", Double.MAX_VALUE),
                    elapsedMs = elapsed,
                )
            )
        } catch (e: IOException) {
            // Nothing came back at all: DNS, refused, reset, timed out. The Mac is off or the
            // tailnet is not up. The distinction between those two is the network callback's,
            // not this probe's.
            return Result.Bad(
                Failure(ProbeFailure.UNREACHABLE, e.javaClass.simpleName, System.currentTimeMillis() - started)
            )
        } finally {
            connection.disconnect()
        }
    }

    private fun readJson(path: String, timeoutMs: Int): JSONObject? {
        val connection = open(path, timeoutMs)
        return try {
            if (connection.responseCode != HttpURLConnection.HTTP_OK) null
            else JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
        } catch (e: Exception) {
            null
        } finally {
            connection.disconnect()
        }
    }

    private fun open(path: String, timeoutMs: Int): HttpsURLConnection {
        // The origin has already been through the allow-list before this class is constructed,
        // so this cannot be pointed at http:// or at another host. The cast is safe for the
        // same reason.
        val connection = URL(origin + path).openConnection() as HttpsURLConnection
        connection.connectTimeout = timeoutMs
        connection.readTimeout = timeoutMs
        connection.useCaches = false
        connection.instanceFollowRedirects = false   // a redirect is not an answer from CROOKS
        connection.setRequestProperty("Accept", "application/json")
        connection.setRequestProperty("Cache-Control", "no-cache")
        return connection
    }

    private companion object {
        /**
         * Four seconds. Long enough for a Mac that is busy starting up on the same tailnet,
         * short enough that a pad showing "Retrying in 2s" is telling the truth rather than
         * sitting inside a fifteen-second socket timeout with a countdown that has run out.
         */
        const val PROBE_TIMEOUT_MS = 4_000

        /** `/health` does real work on the Mac and is asked rarely, so it may take longer. */
        const val HEALTH_TIMEOUT_MS = 10_000
    }
}
