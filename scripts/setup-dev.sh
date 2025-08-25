#!/bin/bash
# Development environment setup script

set -e

echo "🚀 Setting up development environment for FQCN Converter..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📍 Using Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Run initial pre-commit check
echo "✅ Running initial pre-commit check..."
pre-commit run --all-files || echo "⚠️  Some pre-commit checks failed. This is normal for initial setup."

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p docs
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures

echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Available make targets:"
echo "  make help          - Show all available targets"
echo "  make dev-check     - Run all development checks"
echo "  make test          - Run tests"
echo "  make lint          - Run linting"
echo "  make format        - Format code"
echo "  make quality-gate  - Run complete quality checks"
echo ""
echo "Happy coding! 🎉"