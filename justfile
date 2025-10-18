## .justfile for managing python dev tasks
# Inspired by this informative article: https://lukasatkinson.de/2025/just-dont-tox/

## Globals/env 
set dotenv-load := true
dotenv-filename := "_local/.env"

PYTHON_RUNTIME := `echo python$(cat .python-version)`
REPO := `basename "$PWD" | tr ' ' '_'`
VENDOR_DIR := "libs/"
DEPRECATED := "deprecated/"

## Commands 
set shell := ['uv', 'run', 'bash', '-euxo', 'pipefail', '-c']
set positional-arguments 

qa *args: deps lint type_src (test) cov

deps: 
    deptry -e .venv/ -e deprecated/ -e libs/ -e docs/ -e tests/ .

compose: 
    docker compose up -d 

cov: 
    coverage html

test *args:
    coverage run -m pytest -q -s \
      --ignore={{VENDOR_DIR}} \
      tests/ "$@"

lint *args:
    ruff check "$@"

type *args:
    mypy "$@"

type_app: 
    mypy app.py 

type_utils: 
    mypy utils/

type_src: 
    mypy src/

py312 *args: 
    uv run --isolated --group test --python=3.12 pytest -q -s tests/ "$@"

py311 *args: 
    uv run --isolated --group test --python=3.11 pytest -q -s tests/ "$@"