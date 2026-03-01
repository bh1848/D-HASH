.PHONY: install lint format test mypy check clean docker-up docker-down repro

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src tests --fix

format:
	ruff format src tests

mypy:
	mypy src tests

test:
	pytest tests/ -v

check: format lint mypy test

repro:
	dhash-repro --mode all

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
