install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

coverage:
	pytest --cov=greek_tv --cov-report=term-missing

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
