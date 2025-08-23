#!/bin/bash

# Holdem CLI Installation and Test Script
# Run this script to install and test the built package

echo "🎯 Holdem CLI Build Test Script"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo "📦 Installing package..."
pip install dist/holdem_cli-1.0.0b1-py3-none-any.whl --force-reinstall
print_status $? "Package installation"

echo ""
echo "🧪 Testing imports..."

python3 -c "
try:
    from holdem_cli.charts.tui import ChartViewerApp, ChartQuizApp
    print('✅ TUI imports')
except Exception as e:
    print(f'❌ TUI imports: {e}')
    exit(1)

try:
    from holdem_cli.charts.matrix import HandMatrix, HandAction, ChartAction
    print('✅ Matrix imports')
except Exception as e:
    print(f'❌ Matrix imports: {e}')
    exit(1)

try:
    from holdem_cli.charts.cli_integration import ChartManager
    print('✅ CLI integration imports')
except Exception as e:
    print(f'❌ CLI integration imports: {e}')
    exit(1)
"
print_status $? "Core imports"

echo ""
echo "🔧 Testing CLI..."

python3 -c "
import subprocess
import sys

try:
    result = subprocess.run([sys.executable, '-m', 'holdem_cli.cli', '--help'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0 and 'Holdem CLI' in result.stdout:
        print('✅ CLI module works')
    else:
        print(f'❌ CLI module failed: {result.stderr[:100]}...')
        exit(1)
except Exception as e:
    print(f'❌ CLI test failed: {e}')
    exit(1)
"
print_status $? "CLI functionality"

echo ""
echo "🎮 Testing matrix functionality..."

python3 -c "
try:
    from holdem_cli.charts.matrix import HandMatrix, HandAction, ChartAction, create_sample_range
    
    # Create sample range
    sample_range = create_sample_range()
    matrix = HandMatrix(sample_range, 'Test Matrix')
    output = matrix.render(use_colors=False, compact=True)
    
    if output and len(output) > 100:
        print('✅ Matrix rendering works')
    else:
        print('❌ Matrix output too short')
        exit(1)
except Exception as e:
    print(f'❌ Matrix test failed: {e}')
    exit(1)
"
print_status $? "Matrix functionality"

echo ""
echo "🎉 Build test complete!"
echo ""
echo "To use the package:"
echo "1. CLI: holdem --help"
echo "2. Charts: holdem charts view"
echo "3. Quiz: holdem charts quiz sample"
echo ""
echo "Files available in dist/:"
ls -la dist/
