# Holdem CLI - User Guide

Holdem CLI is a terminal-based poker training tool for Texas Hold'em that provides interactive quizzes, simulations, and analytics.

## Quick Start

### Installation

```bash
# Install from PyPI
pip install holdem-cli

# Or install from source
git clone https://github.com/yourusername/holdem-cli.git
cd holdem-cli
pip install -e .
```

### First Time Setup

```bash
# Initialize with your profile
holdem init --profile yourname

### Quick overview of commands

```bash
holdem --help
```

## Core Features

### 🃏 Hand Ranking Quiz

Test your knowledge of poker hand rankings with adaptive difficulty:

```bash
# Basic quiz with adaptive difficulty (recommended)
holdem quiz hand-ranking --count 10

# Specify difficulty level
holdem quiz hand-ranking --difficulty easy --count 5
holdem quiz hand-ranking --difficulty medium --count 5
holdem quiz hand-ranking --difficulty hard --count 5

# Use different profile
holdem quiz hand-ranking --profile coach --count 20
```

**Difficulty Levels:**

- **Adaptive**: Automatically adjusts based on your performance
- **Easy**: Obvious hand differences (e.g., Royal Flush vs High Card)
- **Medium**: Moderate hand differences with some close calls
- **Hard**: Close decisions including kicker battles

### 💰 Pot Odds Quiz

Master pot odds calculations with realistic scenarios:

```bash
# Pot odds training
holdem quiz pot-odds --count 15 --difficulty adaptive

# Focus on specific difficulty
holdem quiz pot-odds --difficulty hard --count 10
```

**Example Question:**

```text
Pot size: $100, Bet to call: $50
You have 9 outs (flush draw).
Should you call this bet?
```

### 🎰 Poker Simulations

Practice against AI opponents with full hand simulation:

```bash
# Play against easy AI
holdem simulate --ai easy

# Challenge yourself with hard AI
holdem simulate --ai hard

# Export hand history for analysis
holdem simulate --ai medium --export-hand my_hand.txt --export-format txt
```

**Available AI Levels:**

- **Easy**: Makes many mistakes, good for learning
- **Medium**: Balanced play with some leaks
- **Hard**: Strong, aggressive play

### 📊 Equity Calculations

Calculate hand equity and win probabilities:

```bash
# Basic hand vs hand
holdem equity AsKs 7h7d

# With board texture
holdem equity AsKs 7h7d --board 2c7s

# Range vs range (Monte Carlo simulation)
holdem equity "AK,AQ,AJ" "77,88,99" --iterations 50000

# JSON output for scripts
holdem equity AsKs 7h7d --json
```

### 📈 Charts and Analysis

Import and study poker charts (GTO ranges, etc.):

```bash
# List available charts
holdem charts list

# View a chart
holdem charts view sample

# Quiz yourself on a chart
holdem charts quiz sample --count 20

# Import your own chart
holdem charts import my_ranges.json
holdem charts export sample my_ranges.txt --format txt
```

## Advanced Features

### 🎯 Adaptive Learning

The quiz system adapts difficulty based on your performance:

- **90%+ accuracy** → Hard difficulty
- **75-89% accuracy** → Medium difficulty
- **60-74% accuracy** → Easy difficulty
- **<60% accuracy** → Easy (with encouragement to practice)

### 📊 Performance Tracking

Track your progress across sessions:

```bash
# View your stats
holdem profile stats yourname

# List all profiles
holdem profile list
```

### 📝 Hand History Export

Export detailed hand histories for analysis:

```bash
# Export as human-readable text
holdem simulate --export-hand analysis.txt --export-format txt

# Export as structured JSON for tools
holdem simulate --export-hand analysis.json --export-format json
```

**Text Format Includes:**

- Session summary (win rate, average pot size)
- Detailed hand-by-hand breakdown
- Card information and final hands
- Betting action sequences
- AI reasoning and player decisions

**JSON Format Includes:**

- Complete session metadata
- Structured betting round data
- Chip stack tracking
- Action history with timestamps
- Export format versioning

## Examples and Workflows

### Beginner Learning Path

```bash
# 1. Start with hand rankings
holdem init --profile beginner
holdem quiz hand-ranking --difficulty easy --count 20

# 2. Learn pot odds
holdem quiz pot-odds --difficulty easy --count 15

# 3. Practice against easy AI
holdem simulate --ai easy

# 4. Check your progress
holdem profile stats beginner
```

### Intermediate Study Session

```bash
# Mix different quiz types
holdem quiz hand-ranking --count 10
holdem quiz pot-odds --count 10

# Study with charts
holdem charts view sample
holdem charts quiz sample --count 15

# Analyze a hand
holdem equity AKs QQ --board JTs
```

### Advanced Analysis Workflow

```bash
# Export multiple hands for review
for i in {1..10}; do
    holdem simulate --ai hard --export-hand "hand_$i.json" --export-format json
done

# Calculate equity for different matchups
holdem equity "AKs,AQs,AJs,ATs" "JJ,QQ,KK" --iterations 50000 --json > range_analysis.json

# Study specific spots
holdem charts create "BTN_vs_BB_3bet" --template balanced
holdem charts quiz "BTN_vs_BB_3bet" --count 30
```

## Tips and Best Practices

### Quiz Strategies

1. **Start Easy**: Build confidence with easier difficulties
2. **Use Adaptive**: Let the system find your optimal difficulty
3. **Mix Quiz Types**: Balance hand ranking and pot odds practice
4. **Track Progress**: Regular quizzes show improvement over time

### Simulation Tips

1. **Start with Easy AI**: Learn proper play before challenging opponents
2. **Export Key Hands**: Save interesting hands for later review
3. **Focus on Position**: Pay attention to position and stack sizes
4. **Review Mistakes**: Use exports to understand where you went wrong

### Performance Optimization

- Use `--iterations 25000` for faster equity calculations
- Use `--export-format txt` for human-readable exports
- Use `--json` output for programmatic processing
- Profile switching lets you track different learning goals

## Troubleshooting

### Common Issues

#### Profile not found

```bash
holdem init --profile yourname
```

#### Database error

```bash
# Reset database
rm -rf ~/Library/Application\ Support/holdem-cli/
holdem init --profile yourname
```

#### Slow performance

```bash
# Use fewer iterations for faster equity calc
holdem equity AKs QQ --iterations 10000
```

### Getting Help

```bash
# See all commands
holdem --help

# Get help for specific command
holdem quiz --help
holdem simulate --help
holdem equity --help

# View examples in this documentation
```

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
