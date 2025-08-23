# Pot Odds Quiz

Master pot odds calculations to make mathematically sound betting decisions in poker.

## Overview

Pot odds quizzes teach you how to calculate whether a bet is profitable based on the relationship between the pot size and the bet amount. This is crucial for making +EV decisions in poker.

## What are Pot Odds?

**Pot Odds** = The ratio of money in the pot compared to the bet you need to call.

**Formula**: `Pot Odds = Bet Amount / (Pot Size + Bet Amount)`

**Example**:
- Pot size: $100
- Bet to call: $50
- Pot odds = $50 / ($100 + $50) = 33%

If your chance of winning is greater than 33%, the call is profitable.

## Quiz Format

### Scenario-Based Questions
Each question presents a realistic poker scenario:

```
Pot size: $120, Bet to call: $40
You have 12 outs (flush draw on turn).
Should you call this bet?

Options:
1. Yes, it's profitable
2. No, it's not profitable
3. Need more information
```

### Difficulty Levels

#### Easy
- Simple calculations
- Clear profitable/unprofitable decisions
- Educational explanations

#### Medium
- More complex scenarios
- Implied odds considerations
- Multiple betting rounds

#### Hard
- Complex multi-way pots
- Semi-bluffing scenarios
- Tournament situations with ICM

## How to Use

### Basic Quiz
```bash
holdem quiz pot-odds --count 10
```

### Difficulty-Specific
```bash
holdem quiz pot-odds --difficulty easy --count 5
holdem quiz pot-odds --difficulty hard --count 15
```

### Adaptive Mode
```bash
holdem quiz pot-odds --count 20
```

## Key Concepts

### 1. Calculating Pot Odds
```
Formula: Odds = Bet / (Pot + Bet)

Examples:
- Pot $100, Bet $25: 25/(100+25) = 20%
- Pot $200, Bet $100: 100/(200+100) = 33%
- Pot $50, Bet $50: 50/(50+50) = 50%
```

### 2. Outs and Equity
- **Outs**: Cards that improve your hand to best
- **Equity**: Your probability of winning the hand

**Common Draw Scenarios:**
- Open-ended straight draw: 8 outs (17% equity)
- Flush draw: 9 outs (19% equity)
- Gutshot straight draw: 4 outs (8% equity)
- Two overcards: 6 outs (12% equity)

### 3. Implied Odds
Consider future betting when calculating if a call is profitable.

**Example**: You're on a flush draw with implied odds of winning a large pot if you hit.

### 4. Fold Equity
When deciding to raise or fold, consider your fold equity (chance opponent folds).

## Learning Strategy

### For Beginners
1. Master basic pot odds calculations
2. Learn common outs for different draws
3. Focus on clear profitable/unprofitable decisions
4. Practice converting percentages to odds

### For Intermediate Players
1. Include implied odds in decisions
2. Consider fold equity
3. Study multi-way pot scenarios
4. Learn tournament-specific situations

### For Advanced Players
1. Factor in ICM (tournament situations)
2. Consider stack sizes and bet sizing
3. Study complex multi-street decisions
4. Analyze opponent tendencies

## Common Scenarios

### Drawing Hands
- **Flush draws**: 9 outs, ~19% equity
- **Straight draws**: 8 outs (open-ended), 4 outs (gutshot)
- **Combination draws**: More complex calculations

### Pre-flop Decisions
- **Set mining**: Pocket pairs vs raises
- **Suited connectors**: Implied odds considerations
- **Speculative hands**: Fold equity decisions

### Post-flop Play
- **Bluffing with equity**
- **Semi-bluffing scenarios**
- **Value betting vs thin value**

## Quick Reference

### Outs to Equity Conversion
- 2 outs: 4% (backdoor straight)
- 4 outs: 8% (gutshot straight)
- 6 outs: 12% (two overcards)
- 8 outs: 17% (open-ended straight)
- 9 outs: 19% (flush draw)
- 12 outs: 25% (flush + straight draw)
- 15 outs: 31% (monster draw)

### Common Pot Odds
- 1:1 (50%): Very good odds
- 1:2 (33%): Decent odds
- 1:3 (25%): Marginal odds
- 1:4 (20%): Poor odds
- 1:5 (17%): Very poor odds

## Tips for Success

1. **Practice Calculations**: Do them in your head quickly
2. **Learn Common Outs**: Memorize equity for frequent draws
3. **Consider Position**: Your position affects decision-making
4. **Factor Implied Odds**: Think about future betting
5. **Study Opponent Tendencies**: Adjust based on opponent play
6. **Manage Bankroll**: Don't risk too much on marginal decisions

## Progress Tracking

Track your improvement:
```bash
holdem profile stats yourname
```

**Target Performance:**
- **80%+ accuracy**: Strong pot odds understanding
- **70-79% accuracy**: Good fundamental knowledge
- **60-69% accuracy**: Developing skills
- **<60% accuracy**: Focus on basic calculations

## Additional Resources

- Study poker math fundamentals
- Practice with small stakes
- Review hand histories
- Discuss scenarios with other players
