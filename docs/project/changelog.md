# Changelog

All notable changes to Holdem CLI will be documented in this file.

## [1.0.0b1] - 2024-01-XX (Beta Release)

### 🎯 Phase 2 Beta Features

#### ✨ Adaptive Difficulty System

- **Adaptive Quizzes**: Quiz difficulty now adjusts automatically based on user performance
- **Performance Analytics**: System tracks accuracy across quiz types (hand ranking, pot odds)
- **Smart Difficulty Selection**: Automatically selects easy/medium/hard based on:
  - 90%+ accuracy → Hard difficulty
  - 75-89% accuracy → Medium difficulty
  - 60-74% accuracy → Easy difficulty
  - <60% accuracy → Easy (with encouragement)

#### 📊 Enhanced Hand History Export

- **Dual Format Support**: Export hand histories as both JSON and human-readable text
- **Session Summaries**: JSON exports include comprehensive session statistics
- **Detailed Text Format**: Human-readable exports with betting action sequences
- **Enhanced JSON Schema**: Structured data with betting rounds, action history, and metadata

#### 📖 Comprehensive Documentation

- **User Guide**: Complete user documentation with examples and workflows
- **Quick Start Guide**: 5-minute setup and basic usage instructions
- **API Reference**: Detailed command reference with all options and examples
- **Example Workflows**: Real-world usage scenarios and teaching examples

### 🔧 Technical Improvements

#### CLI Enhancements

- **Improved Command Structure**: Better argument parsing and validation
- **Enhanced Error Messages**: Clearer feedback for common issues
- **Progress Tracking**: Better integration with user statistics

#### Database Schema Updates

- **User Statistics Tracking**: Enhanced performance metrics storage
- **Adaptive Learning Data**: Storage for difficulty adjustment algorithms
- **Export Metadata**: Better tracking of exported sessions

### 🐛 Bug Fixes

- **Database Migration**: Improved compatibility with existing databases
- **Error Handling**: Better error recovery for edge cases
- **Performance**: Optimized quiz generation and simulation speed

### 📦 Installation & Distribution

- **PyPI Packaging**: Ready for distribution via pip
- **Entry Point Configuration**: Proper CLI installation
- **Dependency Management**: Clear dependency specifications

## [0.1.0] - 2024-01-XX (Alpha Release)

### 🎯 Phase 1 MVP Features

- **Hand Ranking Quiz**: Interactive quiz for poker hand comparisons
- **Pot Odds Quiz**: Pot odds calculation training
- **AI Poker Simulations**: Play against rule-based AI opponents
- **Equity Calculator**: Monte Carlo equity calculations
- **Chart System**: View and quiz on poker strategy charts
- **User Profiles**: Personal progress tracking and statistics
- **SQLite Storage**: Local data persistence

### 🔧 Core Infrastructure

- **CLI Framework**: Click-based command-line interface
- **Database Schema**: User profiles, quiz sessions, simulations, hand histories
- **Card Engine**: Poker card handling and evaluation
- **AI System**: Rule-based opponents with different difficulty levels

## [0.0.1] - 2024-01-XX (Initial Development)

- Project initialization
- Basic CLI structure
- Core engine development
- Database schema design

---

## Versioning Strategy

We use [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, backwards compatible

**Beta versions** (1.0.0b1, 1.0.0b2, etc.) are pre-release versions with new features that may have some instability.

---

## Migration Notes

### Upgrading from 0.1.0 to 1.0.0b1

1. **Database Migration**: Existing databases will be automatically migrated
2. **New Commands**: Adaptive difficulty is now the default for quizzes
3. **Export Format Changes**: Enhanced JSON format with session summaries
4. **Configuration**: Check new CLI options and defaults

### Breaking Changes

None in this beta release. All changes are backwards compatible.

### Deprecation Warnings

- Legacy export formats will be supported through v2.0
- Old database schemas will be migrated automatically
