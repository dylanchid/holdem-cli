# Preflop Starting Hands Quiz

Master preflop poker strategy by learning optimal ranges for different positions and scenarios.

## Overview

The preflop quiz tests your knowledge of which hands to play in various situations before the flop. This is fundamental to poker strategy as preflop decisions account for a significant portion of your overall results.

## Quiz Types

### Position-Based Questions
Learn which hands to play from different positions:

**Example Question:**
```
You're in middle position with 8 players remaining.
Which hands should you raise with?

Select all that apply:
□ A♠ K♠
□ 7♥ 7♦
□ Q♠ J♠
□ A♥ 3♥
□ K♠ Q♠
```

### Scenario-Based Questions
Consider table dynamics, stack sizes, and opponent tendencies:

**Example Question:**
```
You're on the button with a $1000 stack.
Two players have already limped ($20 each).
You look down at J♠ T♠.

What's the optimal play?
1. Fold
2. Call $20
3. Raise to $80
4. Raise to $150
```

## Position Guide

### Early Position (UTG, UTG+1)
- Very tight ranges
- Only premium hands: AA, KK, QQ, AK
- Occasionally strong suited connectors: AQs, AKs, AQo

### Middle Position (MP, MP+1, HJ)
- Expanded ranges
- Premium pairs and suited aces
- Strong suited connectors and broadways
- Some suited connectors: 98s, 87s

### Late Position (CO, Button)
- Much wider ranges
- All premium hands
- Many suited connectors
- Small pairs for set mining
- Suited aces and broadways

### Blinds (SB, BB)
- Even wider ranges when folded to
- Any hand with fold equity
- Small pairs
- Suited connectors
- Any ace

## Key Concepts

### 1. Starting Hand Strength
- **Premium Hands**: AA, KK, QQ, JJ, AKs, AKo, AQs
- **Strong Hands**: TT, 99, AJs, AQo, KQs
- **Speculative Hands**: Small pairs, suited connectors, suited aces

### 2. Position Importance
- Later positions allow wider ranges
- Earlier positions require stronger hands
- Position determines your initiative and information

### 3. Stack Size Considerations
- **Deep stacks**: Play more speculative hands
- **Short stacks**: Focus on premium hands
- **Tournament play**: Consider ICM and bubble factors

### 4. Table Dynamics
- **Tight tables**: Widen your range
- **Loose tables**: Tighten your range
- **Aggressive opponents**: Play more defensively
- **Passive opponents**: Play more aggressively

## How to Use

### Basic Quiz
```bash
holdem quiz preflop --count 10
```

### Position-Specific Practice
```bash
holdem quiz preflop --position early --count 15
holdem quiz preflop --position middle --count 15
holdem quiz preflop --position late --count 15
```

### Scenario-Based
```bash
holdem quiz preflop --scenario --count 20
```

## Learning Strategy

### For Beginners
1. Learn premium hand ranges by position
2. Understand why position matters
3. Study common mistakes to avoid
4. Focus on clear right/wrong scenarios

### For Intermediate Players
1. Learn to adjust ranges based on table dynamics
2. Understand stack size considerations
3. Study tournament vs cash game differences
4. Learn to balance your ranges

### For Advanced Players
1. Fine-tune ranges for specific situations
2. Consider opponent tendencies
3. Master stack size and ICM considerations
4. Study advanced concepts like range balancing

## Common Mistakes

### 1. Playing Too Many Hands from Early Position
```
❌ Playing 7♠ 6♠ from UTG
✅ Folding 7♠ 6♠ from UTG (too speculative)
```

### 2. Folding Too Many Hands from Late Position
```
❌ Folding J♠ T♠ from the button
✅ Raising J♠ T♠ from the button (good speculative hand)
```

### 3. Ignoring Table Dynamics
```
❌ Playing tight range at a loose table
✅ Widening range when opponents are playing many hands
```

### 4. Not Considering Stack Sizes
```
❌ Playing 5♠ 4♠ with $200 stack (too short)
✅ Playing 5♠ 4♠ with $2000 stack (deep enough for implied odds)
```

## Quick Reference Ranges

### Early Position (UTG)
- **Raise**: AA, KK, QQ, JJ, AKs, AKo, AQs, AQo
- **Fold**: Everything else

### Middle Position (MP)
- **Raise**: Above + TT, 99, AJs, KQs, AJo, KQo
- **Call**: Some suited connectors, small pairs

### Late Position (CO/Button)
- **Raise**: Above + 88, 77, A9s, KJs, QJs, JTs, T9s, 98s, 87s, 76s, ATo+, KTo+
- **Call**: More hands with fold equity

### Small Blind
- **Raise**: Any hand worth raising (steal attempt)
- **Call**: Wide range when folded to
- **Fold**: Very rarely when folded to

## Tips for Success

1. **Memorize Premium Hands**: Know them instantly
2. **Understand Position**: Later = wider ranges
3. **Consider Stack Sizes**: Don't play speculative hands short-stacked
4. **Read Table Dynamics**: Adjust based on opponent tendencies
5. **Study Charts**: Use preflop charts as learning tools
6. **Review Mistakes**: Understand why certain plays are correct/incorrect

## Progress Tracking

Monitor your preflop knowledge:
```bash
holdem profile stats yourname
```

**Target Performance:**
- **85%+ accuracy**: Strong preflop fundamentals
- **75-84% accuracy**: Good understanding of ranges
- **65-74% accuracy**: Developing knowledge
- **<65% accuracy**: Focus on basic ranges and position

## Additional Resources

- Study preflop charts from poker books
- Analyze professional player ranges
- Review tournament hands
- Discuss strategy with other players
