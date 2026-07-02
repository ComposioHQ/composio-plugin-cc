.PHONY: help test test-unit validate

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

test: test-unit validate ## Run all checks

test-unit: ## Static validation (frontmatter, manifest, hooks, commands)
	python3 -m pytest tests/unit -q

validate: ## Run `claude plugin validate` on the marketplace + plugin (if claude is installed)
	@if command -v claude >/dev/null 2>&1; then \
		claude plugin validate ./.claude-plugin/marketplace.json && \
		claude plugin validate ./plugins/composio ; \
	else \
		echo "claude CLI not found; skipping validate"; \
	fi
