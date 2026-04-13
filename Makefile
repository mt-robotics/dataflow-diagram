.PHONY: run all help

# Generate one diagram
# Usage: make run IN=docs/mydiagram.json
run:
	uv run python -m dataflow_diagram $(IN) -o $(IN:.json=.svg)

# Regenerate all diagrams in examples/
all:
	for f in examples/*.json; do \
		uv run python -m dataflow_diagram $$f -o $${f%.json}.svg; \
	done

help:
	@echo "Usage:"
	@echo "  make run IN=examples/mydiagram.json   — generate one SVG (output auto-derived)"
	@echo "  make all                               — regenerate all examples/*.json → .svg"
