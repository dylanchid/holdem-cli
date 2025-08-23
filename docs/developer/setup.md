# Development Setup

Complete guide for setting up a development environment for Holdem CLI.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: At least 2GB RAM
- **Storage**: 1GB free space

### Required Tools
- **Git**: Version control system
- **Python pip**: Package management
- **Virtual Environment**: venv or conda

## Quick Setup

### 1. Clone the Repository
```bash
git clone https://github.com/dylanchidambaram/holdem-cli.git
cd holdem-cli
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
holdem --version
```

## Development Environment

### Code Editor/IDE Setup
Recommended editors:
- **VS Code**: Python extension, Pylance
- **PyCharm**: Professional or Community edition
- **Vim/Neovim**: Python syntax highlighting

### Essential Extensions (VS Code)
```
ms-python.python
ms-python.pylint
ms-python.black-formatter
ms-python.isort
ms-python.mypy
```

### Pre-commit Hooks
```bash
# Install pre-commit (if not included in dev dependencies)
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow code style guidelines
- Write tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Lint code
flake8 src/ tests/

# Run tests
pytest --cov=src/holdem_cli
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: your feature description"
```

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/holdem_cli --cov-report=html

# Run specific test file
pytest tests/test_cards.py

# Run specific test
pytest tests/test_cards.py::test_deck_creation
```

### Writing Tests
- Use `pytest` framework
- Place tests in `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test names
- Aim for 80%+ code coverage

### Test Structure
```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = "test input"

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected_output
```

## Code Quality Tools

### Black (Code Formatting)
```bash
# Format code
black src/ tests/

# Check what would be changed
black --check src/ tests/
```

### isort (Import Sorting)
```bash
# Sort imports
isort src/ tests/

# Check import order
isort --check-only src/ tests/
```

### mypy (Type Checking)
```bash
# Type check
mypy src/

# Generate type report
mypy --html-report reports/mypy src/
```

### flake8 (Linting)
```bash
# Lint code
flake8 src/ tests/

# With specific configuration
flake8 --max-line-length=88 src/ tests/
```

## Debugging

### Running in Debug Mode
```bash
# Enable debug logging
export PYTHONPATH=src
python -m pdb -c "b src/holdem_cli/cli.py:100" -m holdem_cli.cli

# Or use VS Code debugger
# Set breakpoints and run debug configuration
```

### Common Debug Techniques
1. **Print statements** for quick debugging
2. **Logging** for production debugging
3. **PDB** for interactive debugging
4. **VS Code debugger** for visual debugging

## Building and Distribution

### Building Package
```bash
# Install build dependencies
pip install build

# Build package
python -m build

# This creates dist/holdem_cli-1.0.0.tar.gz and dist/holdem_cli-1.0.0-py3-none-any.whl
```

### Installing Built Package
```bash
# Install wheel
pip install dist/holdem_cli-1.0.0-py3-none-any.whl

# Test installation
holdem --version
```

## Environment Variables

### Development Variables
```bash
# Enable debug mode
export HOLDEM_DEBUG=1

# Set custom database path
export HOLDEM_DB_PATH=/path/to/custom.db

# Enable performance profiling
export HOLDEM_PROFILE=1
```

### Testing Variables
```bash
# Use test database
export HOLDEM_TEST_DB=1

# Disable external API calls
export HOLDEM_MOCK_EXTERNAL=1
```

## Contributing

See [Contributing Guide](contributing.md) for detailed contribution guidelines.

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/dylanchidambaram/holdem-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dylanchidambaram/holdem-cli/discussions)
- **Documentation**: Check this setup guide and other developer docs
