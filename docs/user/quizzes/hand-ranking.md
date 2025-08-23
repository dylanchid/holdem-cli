# Hand Ranking Quiz

Master the art of comparing poker hands with interactive quizzes designed to build your hand reading skills.

## Overview

The hand ranking quiz tests your ability to compare two poker hands and determine which one is higher. This fundamental skill is crucial for understanding poker strategy and making correct decisions during play.

## Quiz Types

### Standard Hand Ranking
Compare two complete 5-card poker hands to determine the winner.

**Example Question:**
```
Which hand is higher?

Hand 1: A♠ K♠ Q♠ J♠ T♠ (Royal Flush)
Hand 2: A♥ A♦ A♣ K♥ K♦ (Full House)

Enter 1 or 2:
```

### Difficulty Levels

#### Easy
- Obvious hand differences
- Clear ranking separations
- Educational explanations for wrong answers

#### Medium
- Moderate hand differences
- Some close calls requiring careful comparison
- Kicker considerations

#### Hard
- Very close decisions
- Kicker battles
- Split pot scenarios
- Complex hand comparisons

## How to Use

### Basic Quiz
```bash
holdem quiz hand-ranking --count 10
```

### Specify Difficulty
```bash
# Easy mode
holdem quiz hand-ranking --difficulty easy --count 5

# Hard mode
holdem quiz hand-ranking --difficulty hard --count 15
```

### Adaptive Mode (Recommended)
```bash
holdem quiz hand-ranking --count 20
```
The adaptive system automatically adjusts difficulty based on your performance.

## Learning Strategy

### For Beginners
1. Start with easy difficulty
2. Focus on understanding hand rankings
3. Read explanations carefully for wrong answers
4. Practice regularly (10-15 minutes daily)

### For Intermediate Players
1. Use adaptive difficulty
2. Focus on close decisions and kickers
3. Study edge cases and split pots
4. Mix with other quiz types

### For Advanced Players
1. Challenge yourself with hard difficulty
2. Focus on speed and accuracy
3. Study complex hand interactions
4. Use for regular skill maintenance

## Common Mistakes to Avoid

### 1. Ignoring Kickers
```
Hand 1: A♠ A♥ K♠ Q♠ J♠ (Two Aces with K kicker)
Hand 2: A♦ A♣ Q♥ J♥ T♥ (Two Aces with Q kicker)

Hand 1 is higher due to better kicker!
```

### 2. Misunderstanding Hand Strength
```
Hand 1: K♠ K♥ K♦ Q♠ Q♥ (Full House)
Hand 2: A♠ A♥ A♦ 2♠ 2♦ (Full House)

Hand 2 is higher because Aces beat Kings!
```

### 3. Split Pot Confusion
```
Hand 1: A♠ K♠ Q♠ J♠ T♠ (Royal Flush)
Hand 2: A♥ K♥ Q♥ J♥ T♥ (Royal Flush)

This is a split pot - both hands have equal value!
```

## Progress Tracking

### View Your Statistics
```bash
holdem profile stats yourname
```

### Understanding Your Performance
- **90%+ accuracy**: Excellent hand reading skills
- **75-89% accuracy**: Good fundamental knowledge
- **60-74% accuracy**: Room for improvement
- **<60% accuracy**: Focus on basic hand rankings

## Tips for Success

1. **Learn the Rankings**: Memorize the hand hierarchy
2. **Compare Systematically**: Check from highest to lowest rank
3. **Consider Kickers**: Never ignore kicker cards
4. **Practice Regularly**: Daily practice improves recognition speed
5. **Study Mistakes**: Learn from incorrect answers
6. **Mix Difficulties**: Challenge yourself appropriately

## Hand Ranking Hierarchy

1. **Royal Flush** - A♠ K♠ Q♠ J♠ T♠ (same suit)
2. **Straight Flush** - Five cards in sequence, same suit
3. **Four of a Kind** - Four cards of same rank
4. **Full House** - Three of a kind + pair
5. **Flush** - Five cards of same suit
6. **Straight** - Five cards in sequence
7. **Three of a Kind** - Three cards of same rank
8. **Two Pair** - Two pairs of same rank
9. **One Pair** - Two cards of same rank
10. **High Card** - Highest card wins

Remember: Suits are equal - only ranks matter for hand strength!
