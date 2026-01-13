# Usage Guide

## Quick Start

### 1. Setup

```bash
# Run setup script
bash setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

Edit `.env` file and add your API keys:

```bash
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...  # Optional
```

### 3. Index Documentation

```bash
# Index all documentation
python -m src.assistant.cli index

# Or use Makefile
make index
```

### 4. Use the Assistant

```bash
# Interactive mode
python -m src.assistant.cli interactive

# Or
make assistant
```

## Commands

### Help Command

Get answers about the project:

```bash
# General help
python -m src.assistant.cli help

# Specific question
python -m src.assistant.cli help "How does authentication work?"

# Using /help alias
/help How to use the API?
```

### Search Documentation

Search through indexed documentation:

```bash
# Search for a term
python -m src.assistant.cli search "authentication"

# Limit results
python -m src.assistant.cli search "API" --limit 3
```

### Find Related Files

Find files related to a topic:

```bash
python -m src.assistant.cli files "authentication"
```

### Git Context

View git repository information:

```bash
python -m src.assistant.cli git

# Or in interactive mode, just type:
git
```

## Interactive Mode

Start an interactive session:

```bash
python -m src.assistant.cli interactive
```

In interactive mode, you can:

- Ask any question about the project
- Type `git` to see git context
- Type `quit` or `exit` to leave

### Example Session

```
You: How does authentication work?