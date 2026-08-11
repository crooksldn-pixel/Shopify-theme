#!/bin/bash
# Test chromium bare with given extra args; success = title fetched
PW_ARGS=(
--disable-field-trial-config
--disable-background-networking
--disable-background-timer-throttling
--disable-backgrounding-occluded-windows
--disable-back-forward-cache
--disable-breakpad
--disable-client-side-phishing-detection
--disable-component-extensions-with-background-pages
--disable-component-update
--no-default-browser-check
--disable-default-apps
--disable-dev-shm-usage
--disable-edgeupdater
--disable-extensions
"--disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,BlockOriginHeaderModificationOnRedirect,Translate,AutoDeElevate,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion"
--enable-features=CDPScreenshotNewSurface
--allow-pre-commit-input
--disable-hang-monitor
--disable-ipc-flooding-protection
--disable-popup-blocking
--disable-prompt-on-repost
--disable-renderer-backgrounding
--disable-updater-scheduler
--force-color-profile=srgb
--metrics-recording-only
--no-first-run
--password-store=basic
--use-mock-keychain
--no-service-autorun
--export-tagged-pdf
--disable-search-engine-choice-screen
--unsafely-disable-devtools-self-xss-warnings
--edge-skip-compat-layer-relaunch
--disable-infobars
--disable-sync
--enable-unsafe-swiftshader
--hide-scrollbars
--mute-audio
"--blink-settings=primaryHoverType=2,availableHoverTypes=2,primaryPointerType=4,availablePointerTypes=4"
"--proxy-bypass-list=<-loopback>"
)
run_test() {
  local label="$1"; shift
  out=$(timeout 30 /opt/pw-browsers/chromium --headless=new --no-sandbox \
    --proxy-server="http://127.0.0.1:45709" \
    "--disable-features=UseMLKEM,PostQuantumKeyAgreement,PostQuantumKyber" \
    "$@" --dump-dom https://example.com 2>/dev/null | grep -c "Example Domain")
  if [ "$out" -gt 0 ]; then echo "$label: PASS"; else echo "$label: FAIL"; fi
}
run_test "baseline(no extra)"
run_test "ALL playwright args" "${PW_ARGS[@]}"
n=${#PW_ARGS[@]}
half=$((n/2))
run_test "first-half" "${PW_ARGS[@]:0:$half}"
run_test "second-half" "${PW_ARGS[@]:$half}"
