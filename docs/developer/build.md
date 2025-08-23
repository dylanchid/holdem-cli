# Holdem CLI Build v1.0.0b1

## 📦 Built Package Files

The following distribution files have been created:

- `dist/holdem_cli-1.0.0b1-py3-none-any.whl` - Wheel distribution (recommended)
- `dist/holdem_cli-1.0.0b1.tar.gz` - Source distribution

## 🧪 Testing Instructions

### Option 1: Install from Wheel (Recommended)

```bash
# Install the package
pip install dist/holdem_cli-1.0.0b1-py3-none-any.whl

# Test CLI
holdem --help

# Test chart functionality
holdem charts view

# Test quiz functionality
holdem charts quiz sample
```

### Option 2: Install from Source

```bash
# Install from source distribution
pip install dist/holdem_cli-1.0.0b1.tar.gz

# Test same as above
holdem --help
```

### Option 3: Run Tests

```bash
# Run the build test script
python3 test_build.py

# Or test manually
python3 -c "from holdem_cli.charts.tui import ChartViewerApp; print('✅ TUI imports work')"
python3 -c "from holdem_cli.charts.matrix import HandMatrix; print('✅ Matrix imports work')"
```

## 🔧 What's New in This Build

### ✅ Completed Improvements
- **Removed deprecated tui.py file** - Cleaned up import structure
- **Fixed type annotation issues** - Resolved Pylance linter errors
- **Added proper deprecation warnings** - Better user migration experience
- **Maintained backward compatibility** - No breaking changes
- **Improved package structure** - Better organization

### 📁 New Structure
```
src/holdem_cli/charts/
├── matrix.py           ✅ Core visualization (shared)
├── cli_integration.py  ✅ CLI-specific functionality
└── tui/               ✅ TUI-specific components
    ├── __init__.py    ✅ Package exports
    ├── app.py         ✅ Main applications
    ├── widgets.py     ✅ UI components
    ├── constants.py   ✅ Configuration
    ├── messages.py    ✅ Event system
    ├── quiz.py        ✅ Quiz functionality
    └── utils.py       ✅ Utilities
```

## 🚀 Quick Test Commands

```bash
# Install and test
pip install dist/holdem_cli-1.0.0b1-py3-none-any.whl

# Test basic functionality
holdem --help

# Test chart viewing (opens TUI)
holdem charts view

# Test quiz functionality
holdem charts quiz sample --count 5

# List available charts
holdem charts list

# Import a chart
holdem charts import sample_chart.json --name "My Chart"
```

## 🎯 Key Features to Test

1. **CLI Commands**: All chart operations (view, import, export, compare)
2. **TUI Interface**: Interactive chart viewing and editing
3. **Quiz System**: Poker knowledge testing
4. **Import/Export**: Chart file operations
5. **Matrix Rendering**: Hand matrix visualization

## 📊 Version Information

- **Version**: 1.0.0b1 (Beta 1)
- **Python**: >= 3.8
- **Dependencies**: click>=8.0.0, textual>=0.50.0, numpy>=1.20.0
- **Platform**: Cross-platform (Linux, macOS, Windows)

## 🐛 Reporting Issues

If you encounter any issues with this build:

1. Run the test script: `python3 test_build.py`
2. Check the error output
3. Report issues with the specific command that failed

## 📝 Notes

- The package includes the latest TUI improvements
- All imports have been tested and verified
- Backward compatibility is maintained
- The deprecated `tui.py` file has been removed
