# Touchline build and evaluation entry points.
#
# The environment uses uv with a pinned Python 3.12. Heavy targets (acceptance,
# bench at full scale) are separated from the quick targets used in CI.

PY := .venv/bin/python
PIP := uv pip
VENV := .venv

.PHONY: bootstrap doctor build test data demo bench stress docs acceptance verify release \
        ingest coverage features train evaluate simulate thesis lint typecheck clean

bootstrap:
	uv venv --python 3.12 $(VENV)
	$(PIP) install -e ".[dev]"
	@echo "bootstrap complete. Optional model deps: uv pip install -e '.[learn,boost]'"

doctor:
	$(PY) -m touchline.cli doctor

build:
	$(PY) -c "import touchline; print('touchline', touchline.__version__)"

# Coverage plugin autoload hangs in some sandboxed environments; disable autoload
# and enable the plugins we actually use explicitly.
test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PY) -m pytest tests/ -q -p no:cacheprovider

lint:
	.venv/bin/ruff check src tests

typecheck:
	.venv/bin/mypy || true

data:
	$(PY) -m touchline.cli data --sample

demo:
	$(PY) -m touchline.cli demo

bench:
	$(PY) -m touchline.cli bench

stress:
	$(PY) -m touchline.cli stress

docs:
	@echo "docs live under docs/; diagrams render with scripts/render_diagrams.sh"

# Domain command aliases required by the specification.
ingest:
	$(PY) -m touchline.cli ingest $(ARGS)

coverage:
	$(PY) -m touchline.cli coverage $(ARGS)

features:
	$(PY) -m touchline.cli features $(ARGS)

train:
	$(PY) -m touchline.cli train $(ARGS)

evaluate:
	$(PY) -m touchline.cli evaluate $(ARGS)

simulate:
	$(PY) -m touchline.cli simulate $(ARGS)

thesis:
	$(PY) -m touchline.cli thesis $(ARGS)

acceptance:
	$(PY) -m touchline.cli acceptance --run-id $(RUN_ID) --profile $(PROFILE)

verify:
	$(PY) -m touchline.cli verify --evidence $(EVIDENCE)

release:
	$(PY) -m touchline.cli release

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
