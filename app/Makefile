# Makefile na pasta app/ — venv na raiz do repositório (irmão de app/).
APP_MAKEFILE := $(abspath $(firstword $(MAKEFILE_LIST)))
APP_DIR := $(dir $(APP_MAKEFILE))
PROJECT_ROOT := $(abspath $(APP_DIR)..)
VENV := $(abspath $(PROJECT_ROOT)/venv)

ifeq ($(OS),Windows_NT)
	PYTHON := $(VENV)/Scripts/python.exe
else
	PYTHON := $(VENV)/bin/python
endif

PIP := "$(PYTHON)" -m pip
UVICORN := "$(PYTHON)" -m uvicorn

.PHONY: help install run run-prod

help:
	@echo Comandos:
	@echo   make install   - instala dependencias (app/requirements.txt)
	@echo   make run       - sobe a API com reload (porta 8000)
	@echo   make run-prod  - sobe a API sem reload (porta 8000)

install:
	$(PIP) install -r "$(APP_DIR)requirements.txt"

run:
	$(UVICORN) app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir "$(PROJECT_ROOT)"

run-prod:
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --app-dir "$(PROJECT_ROOT)"
