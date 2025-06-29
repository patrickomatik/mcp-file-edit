.PHONY: help install test clean release

help:
	@echo "Available commands:"
	@echo "  make install    - Install the package in development mode"
	@echo "  make test       - Run all tests"
	@echo "  make clean      - Clean up cache and temporary files"
	@echo "  make release    - Prepare for GitHub release"

install:
	uv pip install -e .

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.backup_*" -delete 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

release: clean
	python prepare_release.py
