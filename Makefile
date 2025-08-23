# Docs generation with Sphinx
.PHONY: docs docs-serve docs-clean install run activate

# Use module invocations to avoid relying on shell entry points
SPHINX_BUILD:=uv run python -m sphinx
SPHINX_APIDOC:=uv run python -m sphinx.ext.apidoc
DOCS_SRC:=docs
DOCS_BUILD:=$(DOCS_SRC)/_build/html
API_DIR:=$(DOCS_SRC)/api
PKGS:=gh_pr_rev_md

docs:
	$(SPHINX_APIDOC) -o $(API_DIR) $(PKGS)
	$(SPHINX_BUILD) -b html $(DOCS_SRC) $(DOCS_BUILD)

docs-serve:
	python -m http.server -d $(DOCS_BUILD) 8000

docs-clean:
	rm -rf $(DOCS_SRC)/_build $(API_DIR)

# Create a local virtual environment and install the project (dev dependencies)
install:
	uv venv
	uv pip install '.[dev]'

# Run the CLI via uv (no need to activate PATH)
run:
	uv run gh-pr-rev-md $(ARGS)

# Start a shell with the venv activated (optional)
activate:
	. .venv/bin/activate && echo "Activated: $$(python -V)" && exec $$SHELL -i
