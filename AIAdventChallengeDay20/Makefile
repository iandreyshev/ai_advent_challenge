.PHONY: help setup index clean test assistant

help:
	@echo "RAG Development Assistant - Available commands:"
	@echo ""
	@echo "  make setup       - Setup environment and install dependencies"
	@echo "  make index       - Index project documentation"
	@echo "  make assistant   - Start interactive assistant"
	@echo "  make help-cmd    - Get general help from assistant"
	@echo "  make git         - Show git context"
	@echo "  make clean       - Clean generated files and cache"
	@echo ""

setup:
	@bash setup.sh

index:
	@echo "📚 Indexing documentation..."
	@python -m src.assistant.cli index --clear

assistant:
	@python -m src.assistant.cli interactive

help-cmd:
	@python -m src.assistant.cli help

git:
	@python -m src.assistant.cli git

clean:
	@echo "🧹 Cleaning..."
	@rm -rf data/
	@rm -rf __pycache__/
	@rm -rf src/__pycache__/
	@rm -rf src/*/__pycache__/
	@rm -rf src/*/*/__pycache__/
	@rm -rf *.pyc
	@rm -rf .pytest_cache/
	@echo "✅ Clean complete"

test:
	@echo "🧪 Running tests..."
	@pytest tests/ -v
