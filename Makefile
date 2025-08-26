# Docs generation with Sphinx
.PHONY: help install docs docs-serve docs-clean docs-generate run activate

# Show available make targets
help:
	@echo "Available make targets:"
	@echo ""
	@echo "  Development:"
	@echo "    install       - Create virtual environment and install dev dependencies"
	@echo "    run           - Run the CLI (use ARGS='...' for arguments)"
	@echo "    activate      - Start shell with venv activated"
	@echo ""
	@echo "  Code Quality:"
	@echo "    lint          - Run ruff linting"
	@echo "    lint-fix      - Run ruff with auto-fix"
	@echo ""
	@echo "  Documentation:"
	@echo "    docs-generate - Generate complete documentation with API docs"
	@echo "    docs          - Alias for docs-generate"
	@echo "    docs-serve    - Serve documentation at http://localhost:8000"
	@echo "    docs-clean    - Clean documentation build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make install"
	@echo "  make docs-generate"
	@echo "  make run ARGS='https://github.com/owner/repo/pull/123'"
	@echo "  make docs-serve"

# Create a local virtual environment and install the project (dev dependencies)
install:
	uv venv
	uv pip install '.[dev]'

# Use module invocations to avoid relying on shell entry points
SPHINX_BUILD:=uv run python -m sphinx
SPHINX_APIDOC:=uv run python -m sphinx.ext.apidoc
DOCS_SRC:=docs
DOCS_BUILD:=$(DOCS_SRC)/_build/html
API_DIR:=$(DOCS_SRC)/api
PKGS:=gh_pr_rev_md

# Generate complete documentation including API docs
docs-generate:
	@echo "Generating comprehensive documentation structure..."
	@echo "1. Creating documentation directories..."
	@mkdir -p $(DOCS_SRC)/usage $(DOCS_SRC)/configuration $(DOCS_SRC)/development
	@echo "2. Generating API documentation..."
	$(SPHINX_APIDOC) -f -o $(API_DIR) $(PKGS)
	@echo "3. Building HTML documentation..."
	$(SPHINX_BUILD) -b html $(DOCS_SRC) $(DOCS_BUILD)
	@echo "Documentation generated successfully in $(DOCS_BUILD)"

# Build documentation (legacy target)
docs: docs-generate

docs-serve:
	@echo "Serving documentation at http://localhost:8000"
	python -m http.server -d $(DOCS_BUILD) 8000

docs-clean:
	@echo "Cleaning documentation build artifacts..."
	rm -rf $(DOCS_SRC)/_build $(API_DIR)

.PHONY: lint

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

# Run the CLI via uv (no need to activate PATH)
run:
	uv run gh-pr-rev-md $(ARGS)

# Start a shell with the venv activated (optional)
activate:
	. .venv/bin/activate && echo "Activated: $$(python -V)" && exec $$SHELL -i
