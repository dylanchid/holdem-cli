# Holdem CLI - Examples and Use Cases

This document provides detailed examples and use cases for Holdem CLI.

## 🎯 Quiz Examples

### Hand Ranking Mastery

```bash
# Daily practice routine
holdem quiz hand-ranking --count 20 --difficulty adaptive

# Study specific difficulty
holdem quiz hand-ranking --difficulty hard --count 15 --profile study

# Quick warm-up
holdem quiz hand-ranking --count 5 --difficulty easy
```

### Pot Odds Training

```bash
# Learn to calculate odds
holdem quiz pot-odds --difficulty easy --count 10

# Challenge yourself
holdem quiz pot-odds --difficulty hard --count 20

# Mix with hand rankings for balanced practice
holdem quiz hand-ranking --count 10 && holdem quiz pot-odds --count 10
```

## 🎰 Simulation Examples

### Learning Scenarios

```bash
# Safe learning environment
holdem simulate --ai easy --profile learning

# Test your skills
holdem simulate --ai medium --profile test

# Tournament practice
holdem simulate --ai hard --profile tournament
```

### Analysis and Review

```bash
# Export for detailed review
holdem simulate --ai medium --export-hand review_session_1.txt --export-format txt

# JSON export for programmatic analysis
holdem simulate --ai hard --export-hand analysis_data.json --export-format json

# Multiple hands for pattern analysis
for i in {1..10}; do
    holdem simulate --ai medium --export-hand "hand_$i.json" --export-format json
done
```

## 📊 Equity Calculation Examples

### Basic Comparisons

```bash
# Pocket pairs vs suited connectors
holdem equity "AA,KK,QQ,JJ,TT" "98s,87s,76s,65s"

# Premium vs medium pocket pairs
holdem equity "AKs,AQs,AJs" "77,88,99"

# Race situation
holdem equity "AKo" "QQ" --board "2c7s"
```

### Post-Flop Scenarios

```bash
# Flush draw vs top pair
holdem equity "KsQd" "AcAd" --board "2s7s9s"

# Straight possibilities
holdem equity "89s" "AJs" --board "TQK"

# Turn decision with draws
holdem equity "AhJh" "KdQd" --board "2s7s" --iterations 50000
```

### Range Analysis

```bash
# Button opening range vs BB calling range
holdem equity "22+,A2s+,K2s+,Q2s+,J6s+,T7s+,97s+,86s+,75s+,64s+,53s+,A2o+,K9o+,Q9o+,J9o+,T9o" "22+,A2s+,K2s+,Q2s+,J2s+,T2s+,97s+,86s+,75s+,64s+,53s+,A2o+,K2o+,Q2o+,J2o+,T2o" --iterations 100000

# 3-bet pot analysis
holdem equity "AKs,AQs,AJs,ATs,AQs" "QQ,JJ,TT,99,88" --board "2c7s9h" --iterations 50000
```

## 📈 Chart Analysis Examples

### Chart Creation and Study

```bash
# Create custom chart
holdem charts create "My_Opening_Range" --spot "Early Position Opening"

# Import existing range
holdem charts import my_ranges.json --name "Imported_Range"

# Export for sharing
holdem charts export "My_Opening_Range" shared_range.txt --format txt
```

### Chart Quizzes

```bash
# Practice opening ranges
holdem charts quiz "BTN_Opening_Range" --count 30

# 3-bet defense practice
holdem charts quiz "BB_vs_BTN_3bet" --count 25

# Interactive study session
holdem charts view "UTG_Opening" --interactive
```

## 📝 Advanced Workflows

### Study Session Script

```bash
#!/bin/bash
# Daily study routine

echo "=== Daily Poker Study Session ==="

# Warm-up quizzes
echo "1. Hand Ranking Practice"
holdem quiz hand-ranking --count 10 --difficulty adaptive

echo "2. Pot Odds Practice"
holdem quiz pot-odds --count 8 --difficulty adaptive

# Chart study
echo "3. Chart Analysis"
holdem charts quiz sample --count 15

# Simulation practice
echo "4. Play Practice Hands"
for i in {1..3}; do
    echo "Hand $i vs Medium AI"
    holdem simulate --ai medium --export-hand "practice_hand_$i.txt" --export-format txt
done

# Progress check
echo "5. Progress Review"
holdem profile stats mystudy
```

### Tournament Preparation

```bash
#!/bin/bash
# Tournament preparation script

# Test different stack depths
echo "Testing 20bb strategy"
holdem simulate --ai medium

# Practice specific situations
echo "Practicing bubble play"
holdem simulate --ai hard

# Export for review
holdem simulate --ai hard --export-hand "tournament_prep_$(date +%Y%m%d_%H%M).txt"
```

### Equity Analysis Workflow

```bash
# Create analysis of key matchups
echo "Analyzing key tournament matchups..."

# Race situations
holdem equity AKo QQ --iterations 100000 --json > race_analysis.json
holdem equity AKs JJ --iterations 100000 --json > suited_race.json

# Drawing situations
holdem equity "AhQh" "KK" --board "2s7s" --iterations 50000 --json > flush_draw.json
holdem equity "89s" "AA" --board "TJQ" --iterations 50000 --json > straight_draw.json

# Combine results
echo "Analysis complete. Check JSON files for detailed equity breakdowns."
```

## 🔧 Integration Examples

### Script Integration

```python
#!/usr/bin/env python3
# Batch equity analysis script

import subprocess
import json

def run_equity(hand1, hand2, board="", iterations=25000):
    """Run equity calculation and return parsed result."""
    cmd = f"holdem equity {hand1} {hand2}"
    if board:
        cmd += f" --board {board}"
    cmd += f" --iterations {iterations} --json"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

# Example usage
result = run_equity("AKs", "QQ", "2c7s9h")
print(f"AKs equity: {result['equity']['hand1_win']:.1f}%")
```

### Data Analysis

```python
#!/usr/bin/env python3
# Analyze exported hand history

import json

# Load exported hand history
with open('hand_history.json', 'r') as f:
    data = json.load(f)

# Analyze session
total_hands = data['session_summary']['total_hands']
win_rate = data['session_summary']['player_wins'] / total_hands * 100

print(f"Session Analysis:")
print(f"Hands Played: {total_hands}")
print(f"Win Rate: {win_rate:.1f}%")
print(f"Average Pot Size: ${data['session_summary']['average_pot_size']:.2f}")

# Analyze individual hands
preflop_folds = 0
for hand in data['hands']:
    preflop_actions = [a for round in hand['betting_rounds']
                      if round['street'] == 'preflop'
                      for a in round['actions']]
    if any(a['player'] == 'Human' and a['action'] == 'fold' for a in preflop_actions):
        preflop_folds += 1

print(f"Preflop Fold Rate: {preflop_folds/total_hands*100:.1f}%")
```

## 🎯 Teaching and Coaching

### Student Progress Tracking

```bash
# Create student profiles
holdem init --profile student_alice
holdem init --profile student_bob

# Assign homework
holdem quiz hand-ranking --profile student_alice --count 30
holdem quiz pot-odds --profile student_alice --count 20

# Review progress
holdem profile stats student_alice
holdem profile stats student_bob
```

### Group Analysis

```bash
# Export multiple student sessions
holdem simulate --profile student_alice --export-hand alice_session.txt
holdem simulate --profile student_bob --export-hand bob_session.txt

# Compare performance
# (Use external tools or scripts to compare the exported files)
```

## 🔍 Research and Analysis

### Range Construction

```bash
# Test different range constructions
holdem equity "Broadway: AKo,AQo,AJs,AJo" "Pocket_Pairs: JJ,TT,99" --iterations 100000
holdem equity "Suited_Connectors: 98s,87s,76s,65s" "Same_Pocket_Pairs" --iterations 100000
```

### Spot Analysis

```bash
# Analyze specific poker situations
# 3-bet pot, in position
holdem equity "AKs,AQs,AJs" "QQ" --board "2c7s9h" --iterations 50000

# Blinds vs button
holdem equity "SB_Range: 22+,A2s+,K2s+,Q2s+,J2s+,T2s+,97s+,86s+,75s+,64s+,53s+" "BTN_Range: 22+,A2s+,K9s+,Q9s+,J9s+,T9s,A2o+,K9o+,Q9o+,J9o+,T9o" --iterations 100000
```

## 🚀 Performance Optimization

### Fast Analysis

```bash
# Quick equity checks (fewer iterations)
holdem equity AKs QQ --iterations 10000

# Batch processing with lower precision
holdem equity "AA,KK,QQ" "AKs,AQs,AJs" --iterations 25000
```

### Memory Efficient Processing

```bash
# Process in smaller batches
# Use text format for large exports (smaller file size)
holdem simulate --export-hand large_session.txt --export-format txt
```

This covers the most common use cases and workflows for Holdem CLI. Experiment with different combinations to find what works best for your learning style!
