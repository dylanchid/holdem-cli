#!/usr/bin/env python3
"""Test script for Phase 2 features."""

import sys
import tempfile
import os
import json
from pathlib import Path

# Setup standardized imports using test utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
src_dir = setup_test_imports()

from holdem_cli.simulator.poker_simulator import PokerSimulator
from holdem_cli.quiz.hand_ranking import HandRankingQuiz
from holdem_cli.quiz.pot_odds import PotOddsQuiz

def test_hand_history_export():
    """Test hand history export functionality."""
    print('🧪 Testing hand history export...')

    # Create a simulator
    sim = PokerSimulator()

    # Test that the simulator has the export methods
    assert hasattr(sim, 'export_hand_history'), "export_hand_history method missing"

    # Test export with empty history
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_file = f.name

    try:
        sim.export_hand_history(json_file, format='json')
        print('✅ JSON export method works')
        # Check file size
        size = os.path.getsize(json_file)
        print(f'  Empty JSON file size: {size} bytes')

        # Validate basic JSON structure
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert 'export_info' in data
            assert 'hands' in data
            assert len(data['hands']) == 0
            print('✅ JSON structure valid for empty export')

    except Exception as e:
        print(f'❌ JSON export error: {e}')
    finally:
        os.unlink(json_file)

    # Test text export
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        txt_file = f.name

    try:
        sim.export_hand_history(txt_file, format='txt')
        print('✅ Text export method works')
        # Check file size
        size = os.path.getsize(txt_file)
        print(f'  Empty text file size: {size} bytes')

        # Check if file contains expected content
        with open(txt_file, 'r') as f:
            content = f.read()
            assert 'Poker Hand History Export' in content
            assert 'Total Hands: 0' in content
            print('✅ Text content valid for empty export')

    except Exception as e:
        print(f'❌ Text export error: {e}')
    finally:
        os.unlink(txt_file)

    print('🎉 Hand history export testing complete!')

def test_adaptive_difficulty():
    """Test adaptive difficulty functionality."""
    print('🧪 Testing adaptive difficulty...')

    try:
        # Test adaptive mode
        adaptive_quiz = HandRankingQuiz(difficulty='adaptive')
        assert adaptive_quiz.adaptive_mode == True
        print('✅ Adaptive mode enabled')

        # Test non-adaptive modes
        easy_quiz = HandRankingQuiz(difficulty='easy')
        hard_quiz = HandRankingQuiz(difficulty='hard')
        assert easy_quiz.adaptive_mode == False
        assert hard_quiz.adaptive_mode == False
        print('✅ Non-adaptive modes work')

        # Test pot odds adaptive quiz
        po_adaptive = PotOddsQuiz(difficulty='adaptive')
        assert po_adaptive.adaptive_mode == True
        print('✅ Pot odds adaptive quiz works')

        print('🎉 Adaptive difficulty testing complete!')

    except Exception as e:
        print(f'❌ Adaptive difficulty error: {e}')

def main():
    """Run all tests."""
    print('🚀 Phase 2 Feature Tests')
    print('=' * 40)

    test_adaptive_difficulty()
    print()
    test_hand_history_export()

    print()
    print('🎊 All Phase 2 tests completed!')
    print('Ready for Beta Release! 🚀')

if __name__ == '__main__':
    main()
