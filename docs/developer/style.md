# Code Style Guide

Comprehensive guide to coding standards and best practices for Holdem CLI.

## Python Style Guidelines

### PEP 8 Compliance
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use 4 spaces for indentation (no tabs)
- Limit lines to 88 characters (Black default)
- Use UTF-8 encoding

### Import Organization
```python
# Standard library imports
import os
import sys
from typing import List, Optional

# Third-party imports
import click
import numpy as np

# Local imports
from holdem_cli.engine.cards import Card
from holdem_cli.storage.database import Database
```

### Naming Conventions
- **Variables**: `snake_case` (e.g., `user_name`, `card_value`)
- **Functions**: `snake_case` (e.g., `calculate_equity()`, `validate_hand()`)
- **Methods**: `snake_case` (e.g., `get_user_stats()`, `save_profile()`)
- **Classes**: `PascalCase` (e.g., `PokerHand`, `EquityCalculator`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_ITERATIONS`, `DEFAULT_DIFFICULTY`)
- **Modules**: `snake_case` (e.g., `hand_ranking.py`, `pot_odds.py`)

## Code Formatting

### Black Configuration
```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### isort Configuration
```python
# pyproject.toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["holdem_cli"]
```

## Documentation Standards

### Docstrings
Use Google-style docstrings:

```python
def calculate_equity(hand1: List[Card],
                    hand2: List[Card],
                    board: Optional[List[Card]] = None,
                    iterations: int = 25000) -> float:
    """Calculate hand equity using Monte Carlo simulation.

    Args:
        hand1: First player's hole cards
        hand2: Second player's hole cards
        board: Community cards (optional)
        iterations: Number of Monte Carlo iterations

    Returns:
        Float between 0.0 and 1.0 representing equity percentage

    Raises:
        ValueError: If hands are invalid or iterations < 1

    Example:
        >>> hand1 = [Card('As'), Card('Ks')]
        >>> hand2 = [Card('Ah'), Card('Kh')]
        >>> equity = calculate_equity(hand1, hand2)
        >>> print(f"Equity: {equity:.1%}")
        Equity: 50.0%
    """
```

### Comments
```python
# Good comment - explains why, not what
# Use binary search for performance with large ranges
def find_optimal_hand(hands: List[Hand]) -> Hand:
    pass

# Bad comment - just restates the code
# Find the best hand
def find_best_hand(hands: List[Hand]) -> Hand:
    pass
```

## Type Hints

### Basic Types
```python
from typing import List, Dict, Optional, Union, Any

def process_cards(cards: List[str]) -> Dict[str, Any]:
    """Process card representations."""
    pass

def get_user_profile(user_id: int,
                    include_stats: bool = False) -> Optional[Dict[str, Any]]:
    """Get user profile data."""
    pass
```

### Advanced Types
```python
from typing import NamedTuple, TypedDict

class CardInfo(NamedTuple):
    rank: str
    suit: str
    value: int

class UserStats(TypedDict):
    total_hands: int
    win_rate: float
    avg_profit: float
```

## Error Handling

### Exception Guidelines
```python
# Good - specific exception with context
def load_profile(profile_name: str) -> Profile:
    try:
        return Profile.load(profile_name)
    except FileNotFoundError:
        raise ValueError(f"Profile '{profile_name}' not found")

# Avoid - bare except
try:
    result = risky_operation()
except:  # Don't do this
    pass
```

### Custom Exceptions
```python
class HoldemError(Exception):
    """Base exception for Holdem CLI."""
    pass

class InvalidHandError(HoldemError):
    """Raised when an invalid poker hand is provided."""
    pass

class DatabaseError(HoldemError):
    """Raised when database operations fail."""
    pass
```

## Testing Standards

### Test Structure
```python
import pytest
from holdem_cli.engine.equity import calculate_equity

class TestEquityCalculation:
    def test_equity_basic_calculation(self):
        """Test basic equity calculation."""
        hand1 = [Card('As'), Card('Ks')]
        hand2 = [Card('Ah'), Card('Kh')]

        equity = calculate_equity(hand1, hand2, iterations=1000)

        assert 0.4 <= equity <= 0.6  # Should be close to 50%

    def test_equity_with_board(self):
        """Test equity calculation with community cards."""
        hand1 = [Card('As'), Card('Ks')]
        hand2 = [Card('Ah'), Card('Kh')]
        board = [Card('Ac'), Card('Kc'), Card('Qd')]

        equity = calculate_equity(hand1, hand2, board=board, iterations=1000)

        assert equity > 0.5  # Hand1 should have advantage
```

### Test Coverage
- Aim for 80%+ code coverage
- Test edge cases and error conditions
- Use meaningful test names
- Test both happy path and error scenarios

## Performance Guidelines

### Algorithm Complexity
```python
# Good - O(n) complexity
def find_highest_card(cards: List[Card]) -> Card:
    return max(cards, key=lambda c: c.value)

# Avoid - O(n²) complexity when O(n) is possible
def find_highest_card_slow(cards: List[Card]) -> Card:
    for i, card1 in enumerate(cards):
        is_highest = True
        for card2 in cards:
            if card2.value > card1.value:
                is_highest = False
                break
        if is_highest:
            return card1
```

### Memory Usage
```python
# Good - generator for large datasets
def generate_hands(range_notation: str):
    for hand in parse_range(range_notation):
        yield hand

# Avoid - loading everything into memory
def load_all_hands(range_notation: str) -> List[Hand]:
    return list(parse_range(range_notation))
```

## Security Best Practices

### Input Validation
```python
def validate_card_input(card_str: str) -> bool:
    """Validate card string format."""
    if not isinstance(card_str, str) or len(card_str) != 2:
        return False

    rank, suit = card_str[0], card_str[1]
    return rank in '23456789TJQKA' and suit in 'hdcs'
```

### SQL Injection Prevention
```python
# Good - parameterized queries
cursor.execute("SELECT * FROM users WHERE name = ?", (user_name,))

# Avoid - string formatting
cursor.execute(f"SELECT * FROM users WHERE name = '{user_name}'")
```

## File Organization

### Module Structure
```
holdem_cli/
├── cli.py              # Command-line interface
├── engine/             # Core poker logic
│   ├── cards.py        # Card handling
│   └── equity.py       # Equity calculations
├── quiz/               # Quiz modules
│   ├── hand_ranking.py
│   └── pot_odds.py
├── simulator/          # Simulation logic
└── storage/            # Data persistence
    └── database.py
```

### Package Organization
- Group related functionality in modules
- Keep modules focused and single-purpose
- Use `__init__.py` for package initialization
- Import from parent packages, not individual modules when possible

## Version Control

### Commit Messages
Follow conventional commits:
```bash
feat: add adaptive difficulty system
fix: correct pot odds calculation
docs: update API reference
style: format code with black
refactor: improve database query performance
test: add unit tests for equity calculator
```

### Branch Naming
```bash
feature/add-chart-system
bugfix/fix-equity-calculation
hotfix/critical-database-issue
```

## Code Review Guidelines

### Pull Request Checklist
- [ ] Code follows style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] Code reviewed by at least one other developer
- [ ] All CI checks pass
- [ ] Performance impact assessed

### Review Comments
- Be constructive and specific
- Explain reasoning for suggestions
- Acknowledge good practices
- Focus on code quality and maintainability

## Tools and Configuration

### Development Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting
- **pytest**: Testing
- **coverage**: Coverage reporting

### IDE Configuration
```json
// VS Code settings.json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

This style guide ensures consistency across the codebase and helps maintain high code quality standards.
