export UV_NO_SYNC = 1

all: check test

build:
	uv sync --all-extras --dev

check: build
	uv run ruff check
	uv run mypy

clean:
	git clean -xdf .mypy_cache .pytest_cache .ruff_cache .venv uv.lock

image:
	podman build --tag='localhost/fimfarchive:latest' .

test: build
	uv run pytest
