#!/bin/bash
# Setup script for RAG Development Assistant

echo "🚀 Setting up RAG Development Assistant..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - VOYAGE_API_KEY (optional, will use fallback)"
fi

# Create data directory
mkdir -p data/chromadb

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Index documentation: python -m src.assistant.cli index"
echo "4. Start assistant: python -m src.assistant.cli help"
echo ""
