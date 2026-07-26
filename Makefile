install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

check: lint test

pre-commit:
	pre-commit run --all-files

pre-push:
	pre-commit run --all-files --hook-stage pre-push
