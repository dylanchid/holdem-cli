# Contributing to Holdem CLI

Thank you for your interest in contributing to Holdem CLI! This document provides guidelines for contributing to the project.

## 🏗️ Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- git

### Local Development

1. **Fork and Clone**:

   ```bash
   git clone https://github.com/yourusername/holdem-cli.git
   cd holdem-cli
   ```

2. **Set up Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -e ".[dev]"
   ```

4. **Run Tests**:

   ```bash
   pytest
   ```

5. **Install Pre-commit Hooks** (optional but recommended):

   ```bash
   pre-commit install
   ```

## 🚀 Making Changes

### Development Workflow

1. **Create a Feature Branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**:
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Quality Checks**:

   ```bash
   # Format code
   black src/ tests/

   # Run linting
   flake8 src/ tests/

   # Type checking
   mypy src/

   # Run tests
   pytest --cov=src/holdem_cli
   ```

4. **Commit Your Changes**:

   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create Pull Request**:

   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

#### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

#### TypeScript/React Style (for future TUI)

- Use [ESLint](https://eslint.org/) configuration
- Follow [Prettier](https://prettier.io/) formatting
- Use TypeScript strict mode

#### Commit Messages

Follow [Conventional Commits](https://conventionalcommits.org/):

```text
feat: add new quiz type for Omaha Hi-Lo
fix: correct pot odds calculation for edge cases
docs: update API reference for new commands
style: format code with black
refactor: improve database query performance
test: add unit tests for equity calculator
chore: update dependencies
```

### Testing

#### Unit Tests

- Write tests for all new functions and methods
- Use `pytest` framework
- Place tests in `tests/` directory
- Name test files as `test_*.py`
- Aim for 80%+ code coverage

```python
def test_calculate_pot_odds():
    """Test pot odds calculation."""
    assert calculate_pot_odds(100, 50) == 0.33
    assert calculate_pot_odds(200, 100) == 0.33
```

#### Integration Tests

- Test complete workflows
- Test CLI commands end-to-end
- Test database operations

#### Performance Tests

- Test equity calculation speed
- Test quiz generation performance
- Test simulation speed

### Documentation

- Update docstrings for all public functions
- Update README.md for user-facing changes
- Update API reference for new commands
- Add examples for new features

## 🎯 Feature Development

### Adding New Quiz Types

1. Create quiz class in `src/holdem_cli/quiz/`
2. Implement question generation and validation
3. Add CLI command in `src/holdem_cli/cli.py`
4. Add database schema updates if needed
5. Write comprehensive tests

### Adding New AI Opponents

1. Create AI class in `src/holdem_cli/simulator/`
2. Implement decision-making logic
3. Add configuration options
4. Test against existing benchmarks
5. Document AI strategy and limitations

### Adding New Chart Types

1. Extend chart system in `src/holdem_cli/charts/`
2. Support new import/export formats
3. Add visualization options
4. Update TUI if needed

## 🔧 Pull Request Process

1. **Create Pull Request**:
   - Use descriptive title
   - Reference related issues
   - Provide clear description of changes

2. **Code Review**:
   - Address review comments
   - Ensure all tests pass
   - Verify documentation is updated

3. **Merge**:
   - Squash commits if requested
   - Use merge commit with descriptive message
   - Delete feature branch after merge

## 🐛 Bug Reports

### Good Bug Reports Include

1. **Clear Description**: What went wrong?
2. **Steps to Reproduce**:

   ```bash
   # Commands that reproduce the issue
   holdem quiz hand-ranking --count 5
   ```

3. **Expected Behavior**: What should happen?
4. **Actual Behavior**: What actually happened?
5. **Environment**:
   - OS: macOS 12.0
   - Python: 3.9.0
   - Holdem CLI: 1.0.0b1

### Good Feature Requests Include

1. **Problem Statement**: What's the problem you're trying to solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: What else have you considered?
4. **Use Cases**: When would this feature be used?

## 📋 Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation updates needed
- `help-wanted`: Good for external contributors
- `good-first-issue`: Good for new contributors
- `question`: Question or discussion

## 🌟 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- Project website (future)

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🤝 Code of Conduct

Please be respectful and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/holdem-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/holdem-cli/discussions)
- **Documentation**: [Read the Docs](https://holdem-cli.readthedocs.io/)

Thank you for contributing to Holdem CLI! 🎯🃏
