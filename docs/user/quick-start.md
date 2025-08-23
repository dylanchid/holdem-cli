# Holdem CLI - Quick Start Guide

Get up and running with Holdem CLI in 5 minutes!

## 🚀 Installation

### Option 1: Install from Source (Recommended for now)

```bash
# Clone the repository
git clone https://github.com/yourusername/holdem-cli.git
cd holdem-cli

# Install in development mode
pip install -e .
```

### Option 2: Direct Usage (No install needed)

```bash
# Run directly with Python
python run_holdem.py --help
```

## 🎯 First Steps

### 1. Initialize Your Profile

```bash
# Create your personal profile
holdem init --profile yourname

# Quick overview of what's available
holdem --help
```

### 2. Try Your First Quiz

```bash
# Start with hand rankings (adaptive difficulty)
holdem quiz hand-ranking --count 5

# Try pot odds
holdem quiz pot-odds --count 5
```

### 3. Play Your First Hand

```bash
# Simulate against easy AI
holdem simulate --ai easy
```

### 4. Calculate Some Equity

```bash
# Compare two hands
holdem equity AKs QQ

# Add a board texture
holdem equity AKs QQ --board JTs
```

## 📖 Key Commands

| Command | Description | Example |
|---------|-------------|---------|
| `holdem init` | Set up your profile | `holdem init --profile john` |
| `holdem quiz hand-ranking` | Hand ranking quiz | `holdem quiz hand-ranking --count 10` |
| `holdem quiz pot-odds` | Pot odds quiz | `holdem quiz pot-odds --difficulty easy` |
| `holdem simulate` | Play vs AI | `holdem simulate --ai medium --export-hand hand1.txt` |
| `holdem equity` | Calculate odds | `holdem equity AKs QQ --board 2c7s` |
| `holdem profile stats` | View progress | `holdem profile stats john` |

## 🎮 Game Flow

### Starting a Hand

1. You're dealt 2 cards
2. AI is dealt 2 cards (hidden)
3. Blinds are posted ($10 small, $20 big)

### Making Decisions

- **Preflop**: Decide whether to fold, call, or raise
- **Flop**: 3 community cards dealt - bet/raise/fold
- **Turn**: 4th community card - continue betting
- **River**: 5th community card - final betting
- **Showdown**: If both players remain, compare hands

### Tips for Beginners

- Start with **easy AI** to learn the flow
- Pay attention to **position** (you act last)
- **Export hands** to review mistakes: `--export-hand review.txt`
- Use **adaptive difficulty** for quizzes to match your skill level

## 📊 Understanding Output

### Quiz Results

```text
🃏 Hand Ranking Quiz (Adaptive (Medium) Difficulty)
Score: 8/10 (80.0%)
👍 Good job! You understand most hand rankings well.
```

### Equity Calculation

```text
Equity calculation:
Hand 1: AKs
Hand 2: QQ
Board:   2c7s
Iterations: 25,000

Hand 1 equity: 65.2% win, 8.7% tie, 26.1% lose
Hand 2 equity: 26.1% win, 8.7% tie, 65.2% lose
```

### Simulation

```text
🎰 Starting new hand against easy AI
💰 Starting pot: $30 (blinds posted)
Your cards: As Ks

--- Preflop ---
Your action: (options: call, raise)
```

## 🎯 Next Steps

1. **Practice regularly** - 15 minutes daily works wonders
2. **Export and review** hands you lose
3. **Mix quiz types** - alternate between hand rankings and pot odds
4. **Challenge yourself** - move up AI difficulty as you improve
5. **Track progress** - use `holdem profile stats` to see improvement

## 🆘 Need Help?

```bash
# See all available commands
holdem --help

# Get detailed help for any command
holdem quiz --help
holdem simulate --help

# Check your progress
holdem profile stats yourname
```

## 📈 Learning Path

### Week 1: Basics

- Focus on hand rankings (easy difficulty)
- Learn pot odds calculations
- Play vs easy AI

### Week 2: Intermediate

- Use adaptive difficulty
- Try medium AI
- Start using equity calculator

### Week 3: Advanced

- Hard difficulty quizzes
- Export and analyze hands
- Study with charts

Happy learning! 🃏
