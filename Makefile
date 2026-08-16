PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: venv lint unit actionlint zizmor yamllint ruff pinact check-pins resolve-pins inputs-doc

venv: $(BIN)/ruff

$(BIN)/ruff: requirements-dev.txt
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip
	$(BIN)/pip install --quiet -r requirements-dev.txt
	touch $(BIN)/ruff

lint: venv actionlint zizmor yamllint ruff pinact check-pins

actionlint: venv
	$(BIN)/actionlint -color

zizmor: venv
	$(BIN)/zizmor --persona pedantic .

yamllint: venv
	$(BIN)/yamllint -s .

ruff: venv
	$(BIN)/ruff check scripts tests
	$(BIN)/ruff format --check scripts tests

pinact: $(BIN)/pinact
	$(BIN)/pinact run
	git diff --exit-code -- .github actions examples

$(BIN)/pinact: scripts/install_pinact.sh config/versions.env
	./scripts/install_pinact.sh $(BIN)

check-pins:
	./scripts/check_pins.sh

resolve-pins:
	./scripts/resolve_pins.sh

unit: venv
	$(BIN)/python -m unittest discover -s tests/unit -t . -v

inputs-doc: venv
	$(BIN)/python scripts/gen_inputs_doc.py --write
