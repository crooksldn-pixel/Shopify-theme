VENV := .venv
PY   := $(VENV)/bin/python
# 3.12 preferred; 3.11 is what the suite was verified on. Anything older will not work.
PYTHON ?= $(shell command -v python3.12 || command -v python3.11 || command -v python3)
PIP  := $(VENV)/bin/pip

.PHONY: help doctor venv up install uninstall status restart logs dev bench test test-live lint chat acceptance accept write-check whisper-server secrets shopify gmail gmail-verify voice check test-session-start test-session-status test-session-stop test-session-report test-session-proposals bench-intelligence bench-lanes commands commands-remove update watch

help:
	@echo "The steps you take, in order. Every one is: open Terminal, cd into this folder, type the line."
	@echo ""
	@echo "First time on this Mac:"
	@echo "  make doctor          check the Mac has everything; prints the fix for anything missing"
	@echo "  make venv            install the Python side (once)"
	@echo "  make secrets         store the Shopify credentials and the ElevenLabs key (asks for each)"
	@echo "  make shopify         prove Shopify works and the token cache is used"
	@echo "  make gmail           authorise Gmail once, in a browser"
	@echo "  make test            prove it works here (~6 s, entirely offline)"
	@echo "  make test-live       the two tests that touch the real store and inbox (needs credentials)"
	@echo ""
	@echo "Every day:"
	@echo "  make up              run everything in this one window: backend, speech, HTTPS route"
	@echo "  make install         or: have the Mac start it all at login, no window at all"
	@echo "  make status          is it running, what /health says, the address for the tablet"
	@echo "  make restart         restart the login-time services (after a git pull)"
	@echo "  make uninstall       stop and remove the login-time services"
	@echo "  make logs            follow the login-time services' output"
	@echo ""
	@echo "When something needs looking at:"
	@echo "  make check           doctor + shopify + gmail-verify in one go"
	@echo "  make gmail-verify    prove Gmail refreshes without a browser"
	@echo "  make write-check     rehearse one change through the engine: TOOL=… ARGS='{json}' [COMMIT=1]"
	@echo "  make voice           hear Vikram on this Mac (one short ElevenLabs request)"
	@echo "  make chat            ask questions by typing (cheaper than the tablet)"
	@echo "  make acceptance      the 18-command Day 1 test; add SPOKEN=1 to score spoken runs"
	@echo "  make accept          everything provable without the store: lint, Node, pytest, a server, latency, the page in Chromium"
	@echo "  make dev             the backend alone, with auto-reload, for working on the code"
	@echo "  make whisper-server  speech recognition alone (prints build steps if not built yet)"
	@echo "  make bench           choose the Whisper model from your tablet recordings"
	@echo "  make lint            code style"
	@echo ""
	@echo "An hour with the tablet, written down (nothing restarts; the page joins within a poll):"
	@echo "  make test-session-start [NAME='first hour']   begin; prints the session id"
	@echo "  make test-session-status                      what is running, events so far"
	@echo "  make test-session-stop                        end it"
	@echo "  make test-session-report [SESSION=ts-…]       write reports/<session>.md from logs/test-sessions/<session>.jsonl"
	@echo "  make test-session-proposals [SESSION=ts-…]    write reports/<session>-proposals.md: improvement candidates, cited by turn, never applied"
	@echo "  make bench-intelligence                       time the read layer, the working sets and batch staging against a fake store"
	@echo "  make bench-lanes                              time the fast lane against the 9 September session's own figures"
	@echo "  make watch [SESSION=ts-…]                     follow what it is doing, live, one line per thing"
	@echo ""
	@echo "Three words on the PATH, so none of this needs a folder or a make:"
	@echo "  make commands        install crooks-update, crooks-status and crooks-watch into ~/.local/bin"
	@echo "  crooks-update        pull, install what changed, restart, verify — fast-forward only, never destructive"
	@echo "  crooks-status        one screen: build, voice, Claude, Shopify, Gmail, orders, the tablet's address"
	@echo "  crooks-watch         the live trace"
	@echo "  make commands-remove take them off again"

doctor:
	@$(PY) scripts/doctor.py 2>/dev/null || python3 scripts/doctor.py

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "venv ready."

up:
	$(PY) scripts/up.py

install:
	$(PY) scripts/install_launchd.py

uninstall:
	$(PY) scripts/install_launchd.py --uninstall

status:
	$(PY) scripts/install_launchd.py --status

restart:
	$(PY) scripts/install_launchd.py --restart

logs:
	tail -n 40 -F logs/assistant.out.log logs/assistant.err.log logs/whisper.out.log logs/whisper.err.log

dev:
	$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

whisper-server:
	$(PY) scripts/whisper_server.py

bench:
	$(PY) scripts/bench_whisper.py

test:
	$(VENV)/bin/pytest -q -m "not live"

test-live:
	$(VENV)/bin/pytest -q -m live

lint:
	$(VENV)/bin/ruff check app config scripts tests

chat:
	$(PY) scripts/chat.py

acceptance:
	$(PY) scripts/acceptance.py $(if $(SPOKEN),--spoken,)

write-check:
	$(PY) scripts/write_check.py $(TOOL) '$(ARGS)' $(if $(COMMIT),--commit,)

test-session-start:
	$(PY) scripts/test_session.py start --name "$(if $(NAME),$(NAME),session)"

test-session-status:
	$(PY) scripts/test_session.py status

test-session-stop:
	$(PY) scripts/test_session.py stop

test-session-report:
	$(PY) scripts/test_session.py report $(SESSION)

test-session-proposals:
	$(PY) scripts/test_session.py proposals $(SESSION)

commands:
	@$(PY) scripts/install_commands.py

commands-remove:
	@$(PY) scripts/install_commands.py --remove

update:
	@$(PY) scripts/update.py $(if $(CHECK),--check,)

watch:
	@$(PY) scripts/watch.py $(SESSION)

bench-lanes:
	@$(PY) scripts/bench_lanes.py $(if $(ORDERS),--orders $(ORDERS),) $(if $(LATENCY),--latency-ms $(LATENCY),)

bench-intelligence:
	$(PY) scripts/bench_intelligence.py

accept:
	$(PY) scripts/accept.py $(if $(SHOTS),--shots $(SHOTS),) $(if $(NO_BROWSER),--no-browser,)

secrets:
	$(PY) scripts/set_secrets.py --all

shopify:
	$(PY) scripts/shopify_check.py

gmail:
	$(PY) scripts/gmail_auth.py

gmail-verify:
	$(PY) scripts/gmail_auth.py --verify

voice:
	$(PY) scripts/voice_check.py

check: doctor shopify gmail-verify
