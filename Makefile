
install:
	@echo "Installing dependencies..."
	@poetry install
	@echo "Dependencies installed."


test:
	@echo "Running tests..."
	@poetry run pytest
	@echo "Tests completed."


lint:
	@echo "Running pre-commit hooks..."
	@poetry run pre-commit run --all-files
	@echo "Linting completed."

docsite:
	@echo "Building mkdocs site..."
	@poetry run mkdocs build
	@echo "Documentation built."
	@echo "Serving mkdocs site..."
	@poetry run mkdocs serve
