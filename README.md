# Holdem CLI

A terminal-based poker training tool for Texas Hold'em that provides interactive drills, single-hand simulations, equity calculations, and analytics.

## 🚀 Quick Start

```bash
# Install the package
pip install holdem-cli

# Initialize your profile
holdem init

# Start with a quiz
holdem quiz hand-ranking

# Try the equity calculator
holdem equity AsKs 7h7d
```

## 📖 Documentation

Complete documentation is available in the [docs/](docs/) folder:

### For Users
- **[Quick Start Guide](docs/user/quick-start.md)** - Get up and running in 5 minutes
- **[User Guide](docs/user/guide.md)** - Comprehensive usage guide
- **[Command Reference](docs/user/commands.md)** - Complete CLI reference
- **[Examples](docs/user/examples.md)** - Real-world usage scenarios
- **[Troubleshooting](docs/user/troubleshooting.md)** - Common issues and solutions

### Learning Resources
- **[Hand Ranking Quiz](docs/user/quizzes/hand-ranking.md)** - Master poker hand comparisons
- **[Pot Odds Quiz](docs/user/quizzes/pot-odds.md)** - Learn pot odds calculations
- **[Preflop Starting Hands](docs/user/quizzes/preflop.md)** - Study optimal preflop ranges

### For Developers
- **[Development Setup](docs/developer/setup.md)** - Environment setup and local development
- **[Contributing Guide](docs/developer/contributing.md)** - How to contribute to the project
- **[Code Style Guide](docs/developer/style.md)** - Coding standards and conventions
- **[API Reference](docs/developer/api.md)** - Complete API documentation

### Project Information
- **[Changelog](docs/project/changelog.md)** - Version history and release notes
- **[Database Schema](docs/developer/database.md)** - Data persistence and models

## ✨ Features

- **Interactive Quizzes**: Hand ranking, pot odds, pre-flop starting hands
- **Hand Simulator**: Full hand cycles against rule-based AI
- **Equity Calculator**: Monte Carlo simulations for hand vs hand analysis
- **Progress Tracking**: Local SQLite database stores your stats
- **Offline First**: No internet required for core functionality

## 🏗️ Architecture

- `src/holdem_cli/engine/`: Core poker logic (deck, evaluator, Monte Carlo)
- `src/holdem_cli/cli/`: Command-line interface
- `src/holdem_cli/storage/`: SQLite persistence layer
- `src/holdem_cli/quiz/`: Quiz generation and scoring
- `src/holdem_cli/simulator/`: Hand simulation against AI

## 🛠️ Development

```bash
# Clone and setup
git clone https://github.com/dylanchid/holdem-cli.git
cd holdem-cli
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
```

## 📚 Additional Resources

- **[Product Requirements](docs/developer/prd.md)** - Detailed product specifications
- **[Implementation Notes](docs/developer/implementation.md)** - Technical implementation details
- **[Performance Guide](docs/developer/performance.md)** - Optimization and performance tuning

For the complete documentation index, see **[docs/index.md](docs/index.md)**.
