VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

.PHONY: help doctor venv dev bench test lint chat acceptance whisper-server

help:
	@echo "make doctor      — check every prerequisite and print versions"
	@echo "make venv        — create .venv and install dependencies"
	@echo "make dev         — run the backend on 127.0.0.1:8000"
	@echo "make whisper-server — run whisper.cpp server on 127.0.0.1:8910"
	@echo "make bench       — benchmark Whisper models over bench/audio/"
	@echo "make test        — pytest (live API tests skipped without credentials)"
	@echo "make lint        — ruff check"
	@echo "make chat        — terminal REPL against /turn"
	@echo "make acceptance  — run the 18-command Day 1 acceptance script"

doctor:
	@$(PY) scripts/doctor.py 2>/dev/null || python3 scripts/doctor.py

venv:
	python3.12 -m venv $(VENV)
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
	$(PY) scripts/acceptance.py
