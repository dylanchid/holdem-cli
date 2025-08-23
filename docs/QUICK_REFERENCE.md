# 🎯 Holdem CLI - Quick Reference Guide

## ⚡ Essential Shortcuts

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `↑↓←→` | Navigate Matrix | Move through 13x13 hand matrix |
| `WASD` | Navigate Matrix | Alternative navigation keys |
| `Enter/Space` | Select Hand | View details for current hand |
| `Home` | Jump to AA | Go to top-left corner |
| `End` | Jump to 32 | Go to bottom-right corner |

### Position Shortcuts
| Key | Position | Location |
|-----|----------|----------|
| `1` | Under the Gun (UTG) | Top-left area |
| `2` | Middle Position (MP) | Middle-left area |
| `3` | Cutoff (CO) | Bottom-middle area |
| `4` | Button (BTN) | Bottom-right area |
| `5` | Small Blind (SB) | Middle area |
| `6` | Big Blind (BB) | Lower-middle area |

### View Controls
| Key | Action | Description |
|-----|--------|-------------|
| `F` | Toggle Frequency | Show action percentages |
| `V` | Toggle EV | Show expected value data |
| `M` | Cycle View Modes | Rotate through all view modes |
| `R` | Reset View | Return to default state |

### Range Builder
| Key | Action | Description |
|-----|--------|-------------|
| `B` | Toggle Range Builder | Enter/exit range builder mode |
| `A` | Add Hand | Add current hand to custom range |
| `D` | Remove Hand | Remove current hand from custom range |
| `C` | Clear Range | Clear all hands from custom range |

### Search & Filtering
| Key | Action | Description |
|-----|--------|-------------|
| `/` | Open Search | Start hand search |
| `N` | Next Result | Navigate to next search result |
| `Shift+N` | Previous Result | Navigate to previous search result |

### Chart Operations
| Key | Action | Description |
|-----|--------|-------------|
| `Ctrl+L` | Load Chart | Load chart from file |
| `Ctrl+S` | Save Chart | Save current chart |
| `Ctrl+E` | Export Chart | Export in multiple formats |
| `Ctrl+C` | Compare Charts | Compare two charts |

### Tab Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `Tab` | Next Tab | Switch to next interface tab |
| `Shift+Tab` | Previous Tab | Switch to previous interface tab |
| `Ctrl+T` | New Chart Tab | Create new chart tab |
| `Ctrl+W` | Close Tab | Close current tab |

### General
| Key | Action | Description |
|-----|--------|-------------|
| `H` | Help | Open comprehensive help system |
| `Q` | Quit | Exit the application |
| `Escape` | Clear/Close | Clear current mode or close dialog |

---

## 🔍 Search Query Examples

### Hand Names
```
"AK"     → Find all AK hands (AKs, AKo)
"JJ"     → Find pocket Jacks
"A5"     → Find all A5 hands (A5s, A5o)
```

### Hand Types
```
"suited"      → Find all suited hands (ends with 's')
"offsuit"     → Find all offsuit hands (ends with 'o')
"pocket"      → Find all pocket pairs (AA, KK, etc.)
"broadway"    → Find broadway cards (AKQJT)
"connector"   → Find connected hands
```

### Actions
```
"raise"  → Find all hands with raise action
"call"   → Find all hands with call action
"fold"   → Find all hands with fold action
"mixed"  → Find all hands with mixed actions
```

### Premium Hands
```
"premium"  → Find premium hands (AA, KK, QQ, JJ, AK)
"high"     → Find high cards (AKQJ)
"low"      → Find low cards (23456)
```

---

## 📊 View Modes Explained

### Range View (Default)
- **Colors**: Actions shown with colored squares
  - 🔴 Red = Raise actions
  - 🟢 Green = Call actions
  - ⚫ Gray = Fold actions
  - 🟡 Yellow = Mixed actions
- **Display**: Hand notation (AKs, 7h6h, etc.)

### Frequency View (`F`)
- **Numbers**: Shows action frequency as percentages
- **Colors**: Green (80%+), Yellow (50-79%), Red (<50%)
- **Example**: `85%`, `67%`, `23%`

### EV View (`V`)
- **Numbers**: Shows expected value (EV) in bb/100
- **Colors**: Green (positive), Yellow (break-even), Red (negative)
- **Example**: `+2.3`, `+0.8`, `-1.5`

---

## 🎨 Notification System

### Success Messages ✅
```
✅ Chart saved successfully! (42 hands)
✅ Switched to frequency view
✅ Tight range loaded successfully
```

### Warning Messages ⚠️
```
⚠️ No chart data to save
⚠️ Cannot close main chart tab
⚠️ Search returned no results
```

### Error Messages ❌
```
❌ Failed to load chart: File not found
❌ Permission denied: Cannot write to file
❌ Navigation error: Invalid position
```

### Progress Messages 📊
```
📊 Exporting chart... 75%
🔄 Processing data... Please wait
📈 Analyzing statistics... Done
```

---

## 📁 File Operations

### Supported Formats
- **JSON**: Structured data with metadata
- **CSV**: Spreadsheet-compatible format
- **TXT**: Human-readable text format

### Export Features
- **Multi-format**: Export in all formats simultaneously
- **Metadata**: Includes chart statistics and analysis
- **Validation**: Ensures data integrity before export

### Import Features
- **Auto-detection**: Automatically detects file format
- **Validation**: Validates chart data during import
- **Error Recovery**: Handles corrupted or invalid files gracefully

---

## 💡 Quick Tips

### Getting Started
1. Press `H` to open the help system
2. Use arrow keys to navigate the matrix
3. Press `Enter` to select a hand
4. Try `1-6` to jump to different positions

### Efficient Workflow
- **Search First**: Use `/` to find specific hands quickly
- **Position Jumps**: Use `1-6` for position-specific analysis
- **View Cycling**: Press `M` to see different perspectives
- **Regular Saving**: Use `Ctrl+S` to prevent data loss

### Performance
- **Close Unused Tabs**: Use `Ctrl+W` to free memory
- **Use Statistics Wisely**: Complex stats are cached for speed
- **Batch Operations**: Export multiple charts efficiently

---

## 🎓 Learning Resources

### Built-in Help
- **H**: Comprehensive help system
- **Contextual Help**: Situation-aware guidance
- **Interactive Tutorial**: Step-by-step learning
- **Searchable Documentation**: Find help topics quickly

### External Resources
- **Chart Analysis**: Learn from AI-powered statistics
- **Range Optimization**: Get strategic recommendations
- **Performance Tracking**: Monitor your improvement over time

---

## 🚨 Emergency Shortcuts

| Situation | Solution |
|-----------|----------|
| **Stuck in mode** | Press `Escape` to clear current mode |
| **Lost navigation** | Press `R` to reset to default view |
| **Can't find hand** | Press `/` to search for specific hands |
| **High memory usage** | Press `Ctrl+W` to close current tab |
| **Need help** | Press `H` for context-sensitive help |

---

*Remember: Press `H` at any time for comprehensive help and guidance!*

**🎯 Happy charting!**
