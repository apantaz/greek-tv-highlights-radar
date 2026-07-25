install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .
