VENV := .venv
PY   := $(VENV)/bin/python
# 3.12 preferred; 3.11 is what the suite was verified on. Anything older will not work.
PYTHON ?= $(shell command -v python3.12 || command -v python3.11 || command -v python3)
PIP  := $(VENV)/bin/pip

.PHONY: help doctor venv dev bench test lint chat acceptance whisper-server secrets shopify gmail gmail-verify check

help:
	@echo "The steps you take, in order. Every one is: open Terminal, cd into this folder, type the line."
	@echo ""
	@echo "  make doctor          check the Mac has everything; prints the fix for anything missing"
	@echo "  make venv            install the Python side (once)"
	@echo "  make test            prove it works here (~3 s)"
	@echo "  make dev             start the backend, then: tailscale serve 8000"
	@echo "  make whisper-server  start speech recognition (prints build steps if not built yet)"
	@echo "  make bench           choose the Whisper model from your tablet recordings"
	@echo "  make secrets         store the Claude token and Shopify credentials (asks for each)"
	@echo "  make shopify         prove Shopify works and the token cache is used"
	@echo "  make gmail           authorise Gmail once, in a browser"
	@echo "  make gmail-verify    prove Gmail refreshes without a browser"
	@echo "  make check           doctor + shopify + gmail-verify in one go"
	@echo "  make chat            ask questions by typing (cheaper than the tablet)"
	@echo "  make acceptance      the 18-command Day 1 test; add SPOKEN=1 to score spoken runs"
	@echo "  make lint            code style"

doctor:
	@$(PY) scripts/doctor.py 2>/dev/null || python3 scripts/doctor.py

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "venv ready — activate with: source $(VENV)/bin/activate"

dev:
	$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

whisper-server:
	$(PY) scripts/whisper_server.py

bench:
	$(PY) scripts/bench_whisper.py

test:
	$(VENV)/bin/pytest -q

lint:
	$(VENV)/bin/ruff check app config scripts tests

chat:
	$(PY) scripts/chat.py

acceptance:
	$(PY) scripts/acceptance.py $(if $(SPOKEN),--spoken,)

secrets:
	$(PY) scripts/set_secrets.py --all

shopify:
	$(PY) scripts/shopify_check.py

gmail:
	$(PY) scripts/gmail_auth.py

gmail-verify:
	$(PY) scripts/gmail_auth.py --verify

check: doctor shopify gmail-verify
