@echo off
REM Development environment setup script for Windows

echo 🚀 Setting up development environment for FQCN Converter...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.8 or later.
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo 📍 Using Python %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install development dependencies
echo 📚 Installing development dependencies...
pip install -e ".[dev]"

REM Install pre-commit hooks
echo 🪝 Installing pre-commit hooks...
pre-commit install

REM Run initial pre-commit check
echo ✅ Running initial pre-commit check...
pre-commit run --all-files
if %errorlevel% neq 0 (
    echo ⚠️  Some pre-commit checks failed. This is normal for initial setup.
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "docs" mkdir docs
if not exist "tests\unit" mkdir tests\unit
if not exist "tests\integration" mkdir tests\integration
if not exist "tests\fixtures" mkdir tests\fixtures

echo.
echo ✨ Development environment setup complete!
echo.
echo To activate the virtual environment, run:
echo   .venv\Scripts\activate.bat
echo.
echo Available make targets (if you have make installed):
echo   make help          - Show all available targets
echo   make dev-check     - Run all development checks
echo   make test          - Run tests
echo   make lint          - Run linting
echo   make format        - Format code
echo   make quality-gate  - Run complete quality checks
echo.
echo Happy coding! 🎉

pause