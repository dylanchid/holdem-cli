# Holdem CLI - API Reference

This document provides detailed API reference for Holdem CLI commands and options.

## Command Line Interface

### Global Options

All commands support these global options:

| Option | Description | Default |
|--------|-------------|---------|
| `--help` | Show help message and exit | - |
| `--version` | Show version information | - |

## Core Commands

### `holdem init`

Initialize Holdem CLI with a new profile and database.

```bash
holdem init [OPTIONS]
```

**Options:**

- `--profile TEXT`: Profile name to use [default: default]

**Examples:**

```bash
holdem init --profile john
holdem init  # Uses 'default' profile
```

### `holdem quiz`

#### `holdem quiz hand-ranking`

Interactive quiz for testing poker hand ranking knowledge.

```bash
holdem quiz hand-ranking [OPTIONS]
```

**Options:**

- `--count INTEGER`: Number of questions [default: 10]
- `--profile TEXT`: Profile to use [default: default]
- `--difficulty [adaptive|easy|medium|hard]`: Quiz difficulty [default: adaptive]

**Examples:**

```bash
holdem quiz hand-ranking --count 20 --difficulty adaptive
holdem quiz hand-ranking --difficulty hard --profile study
```

#### `holdem quiz pot-odds`

Interactive quiz for testing pot odds calculation knowledge.

```bash
holdem quiz pot-odds [OPTIONS]
```

**Options:**

- `--count INTEGER`: Number of questions [default: 10]
- `--profile TEXT`: Profile to use [default: default]
- `--difficulty [adaptive|easy|medium|hard]`: Quiz difficulty [default: adaptive]

**Examples:**

```bash
holdem quiz pot-odds --count 15 --difficulty medium
holdem quiz pot-odds --difficulty adaptive --profile practice
```

### `holdem simulate`

Simulate a complete poker hand against AI opponent.

```bash
holdem simulate [OPTIONS]
```

**Options:**

- `--ai [easy|medium|hard]`: AI difficulty level [default: easy]
- `--profile TEXT`: Profile to use [default: default]
- `--export-hand TEXT`: Export hand history to file
- `--export-format [json|txt]`: Export format for hand history [default: json]

**Examples:**

```bash
holdem simulate --ai medium
holdem simulate --ai hard --export-hand my_hand.json --export-format json
holdem simulate --export-hand review.txt --export-format txt
```

### `holdem equity`

Calculate equity between two hands using Monte Carlo simulation.

```bash
holdem equity [OPTIONS] HAND1 HAND2
```

**Arguments:**

- `HAND1`: First hand (e.g., AsKs, 7h7d)
- `HAND2`: Second hand (e.g., QhQd, JTs)

**Options:**

- `--board TEXT`: Board cards (e.g., 2c7s)
- `--iterations INTEGER`: Monte Carlo iterations [default: 25000]
- `--json`: Output as JSON
- `--seed INTEGER`: Random seed for deterministic results

**Examples:**

```bash
holdem equity AsKs 7h7d
holdem equity AsKs 7h7d --board 2c7s --iterations 50000
holdem equity "AKs,AQs" "JJ,QQ" --json
```

## Chart Commands

### `holdem charts list`

List all saved charts.

```bash
holdem charts list
```

### `holdem charts view`

View a specific chart.

```bash
holdem charts view [OPTIONS] CHART_NAME
```

**Arguments:**

- `CHART_NAME`: Name of the chart to view

**Options:**

- `--interactive, -i`: Launch interactive TUI
- `--compact`: Use compact display
- `--no-color`: Disable colors

**Examples:**

```bash
holdem charts view sample
holdem charts view "BTN vs BB" --interactive
holdem charts view my-chart --compact --no-color
```

### `holdem charts quiz`

Quiz yourself on a chart.

```bash
holdem charts quiz [OPTIONS] CHART_NAME
```

**Arguments:**

- `CHART_NAME`: Name of the chart to quiz on

**Options:**

- `--count, -c INTEGER`: Number of questions [default: 20]
- `--interactive, -i`: Interactive quiz mode
- `--profile TEXT`: Profile to save results [default: default]

**Examples:**

```bash
holdem charts quiz sample --count 30
holdem charts quiz "BTN vs BB" --interactive
```

### `holdem charts create`

Create a new chart.

```bash
holdem charts create [OPTIONS] NAME
```

**Arguments:**

- `NAME`: Name for the new chart

**Options:**

- `--spot TEXT`: Poker spot description
- `--depth INTEGER`: Stack depth in BB [default: 100]
- `--template [tight|loose|balanced]`: Use a template as starting point

**Examples:**

```bash
holdem charts create "My BTN Range"
holdem charts create "Loose 3bet" --template loose --depth 200
```

### `holdem charts import`

Import chart from file.

```bash
holdem charts import [OPTIONS] FILEPATH
```

**Arguments:**

- `FILEPATH`: Path to chart file

**Options:**

- `--format, -f [json|simple]`: Input file format [default: json]
- `--name TEXT`: Chart name (default: filename)
- `--spot TEXT`: Poker spot description
- `--depth INTEGER`: Stack depth in BB [default: 100]

**Examples:**

```bash
holdem charts import my_chart.json
holdem charts import ranges.txt --format simple --name "My Range"
```

### `holdem charts export`

Export chart to file.

```bash
holdem charts export [OPTIONS] CHART_NAME OUTPUT_PATH
```

**Arguments:**

- `CHART_NAME`: Name of the chart to export
- `OUTPUT_PATH`: Output file path

**Options:**

- `--format, -f [json|txt|csv]`: Output format [default: txt]

**Examples:**

```bash
holdem charts export sample my_chart.txt
holdem charts export "BTN vs BB" ranges.json --format json
holdem charts export my-chart data.csv --format csv
```

## Profile Commands

### `holdem profile list`

List all profiles.

```bash
holdem profile list
```

### `holdem profile stats`

Show statistics for a profile.

```bash
holdem profile stats [OPTIONS] NAME
```

**Arguments:**

- `NAME`: Name of the profile to show stats for

**Examples:**

```bash
holdem profile stats john
holdem profile stats coach
```

## Data Formats

### Hand Notation

Hands are specified using standard poker notation:

- **Individual cards**: `As` (Ace of spades), `7h` (7 of hearts)
- **Hole cards**: `AsKs` (Ace of spades, King of spades)
- **Board**: `2c7s9h` (2 of clubs, 7 of spades, 9 of hearts)
- **Ranges**: `"AKs,AQs,AJs"` (comma-separated list)

### JSON Output Format

#### Equity Calculation

```json
{
  "hand1": "AsKs",
  "hand2": "7h7d",
  "board": "2c7s",
  "equity": {
    "hand1_win": 65.2,
    "hand1_tie": 8.7,
    "hand1_lose": 26.1,
    "hand2_win": 26.1,
    "hand2_tie": 8.7,
    "hand2_lose": 65.2,
    "total_simulations": 25000
  }
}
```

#### Hand History Export

```json
{
  "export_info": {
    "export_date": "2024-01-15T10:30:00",
    "ai_level": "medium",
    "export_format": "holdem-cli-v2",
    "version": "1.0"
  },
  "session_summary": {
    "total_hands": 5,
    "player_wins": 3,
    "ai_wins": 2,
    "ties": 0,
    "showdowns": 4,
    "average_pot_size": 85.0
  },
  "hands": [
    {
      "hand_number": 1,
      "timestamp": "2024-01-15T10:30:00",
      "winner": "Human",
      "pot_size": 120,
      "cards": {
        "player": ["As", "Ks"],
        "ai": ["Qh", "Qd"],
        "board": ["2c", "7s", "9h", "Tc", "Jd"]
      },
      "betting_rounds": [...]
    }
  ]
}
```

### Text Export Format

Hand history text export includes:

- Session summary with statistics
- Individual hand breakdowns
- Card information
- Betting action sequences
- Final hand evaluations

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Profile not found |
| 4 | Database error |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOLDEM_DB_PATH` | Custom database path | Platform-specific |
| `HOLDEM_DEBUG` | Enable debug output | false |

## File Paths

### Database Location

- **macOS**: `~/Library/Application Support/holdem-cli/holdem-cli.db`
- **Linux**: `~/.local/share/holdem-cli/holdem-cli.db`
- **Windows**: `%APPDATA%\holdem-cli\holdem-cli.db`

### Configuration

Configuration is stored alongside the database in the application support directory.

## Performance Notes

### Equity Calculation Performance

- Default: 25,000 iterations (good balance of speed/accuracy)
- Fast: 10,000 iterations (quick analysis)
- Accurate: 100,000+ iterations (research quality)

### Memory Usage

- Base memory: ~50MB
- Per simulation: ~1MB additional
- Chart loading: ~10MB per large chart

### CPU Usage

- Single equity calculation: 1-2 seconds on modern hardware
- Quiz processing: Minimal CPU usage
- Simulation: 100-500ms per betting decision

This reference covers all public APIs. For internal APIs and development, see the source code documentation.
