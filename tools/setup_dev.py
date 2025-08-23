#!/usr/bin/env python3
"""Development setup script for Holdem CLI."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print("✅ Success!")
            if result.stdout.strip():
                print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Set up development environment."""
    print("🎰 Setting up Holdem CLI development environment...")
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Install in development mode
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], 
                      "Installing Holdem CLI in development mode"):
        print("Failed to install package. Try running manually:")
        print("  pip install -e .")
        return False
    
    # Install dev dependencies
    if not run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], 
                      "Installing development dependencies"):
        print("Warning: Failed to install dev dependencies")
    
    # Add src to path for development
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    
    # Run basic tests
    print("\n🧪 Running basic functionality tests...")
    try:
        # Import and test basic functionality
        from holdem_cli.engine.cards import Card, Deck
        from holdem_cli.engine.equity import EquityCalculator, parse_hand_string
        
        # Test card creation
        card = Card.from_string("As")
        print(f"✅ Created card: {card}")
        
        # Test deck
        deck = Deck()
        deck.shuffle()
        hand = deck.deal(2)
        print(f"✅ Dealt hand: {', '.join(str(c) for c in hand)}")
        
        # Test equity
        calculator = EquityCalculator()
        aces = parse_hand_string("AsAh")
        kings = parse_hand_string("KsKh")
        print("✅ Parsed hands successfully")
        
        print("\n🎉 Basic setup complete!")
        print("\nNext steps:")
        print("  holdem init                    # Initialize your profile")
        print("  holdem quiz hand-ranking       # Try a quiz")
        print("  holdem equity AsKs 7h7d        # Calculate equity")
        print("  holdem simulate                # Play against AI")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
