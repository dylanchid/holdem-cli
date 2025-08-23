"""
Unified service layer for Holdem CLI.

This module provides a unified interface to all Holdem CLI functionality,
eliminating duplicate logic between CLI and TUI components.

Services provided:
- Quiz management (hand ranking, pot odds)
- Equity calculations
- Poker simulations
- Chart management
- Profile management
- Database operations
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

from ..storage import Database, init_database, get_database_path
from ..engine.equity import EquityCalculator, parse_hand_string
from ..engine.cards import Card
from ..quiz.hand_ranking import HandRankingQuiz
from ..quiz.pot_odds import PotOddsQuiz
from ..simulator.poker_simulator import PokerSimulator
from holdem_cli.types import HandAction, ChartAction
from holdem_cli.charts.tui.widgets.matrix import HandMatrix, create_sample_range
from ..charts.chart_cli import ChartManager


class HoldemService:
    """Unified service for all Holdem CLI functionality."""

    def __init__(self):
        """Initialize the service with database connection."""
        self.db = init_database()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if hasattr(self, 'db'):
            self.db.close()

    # ============================================================================
    # PROFILE MANAGEMENT
    # ============================================================================

    def create_profile(self, profile_name: str) -> Tuple[bool, str]:
        """Create a new user profile."""
        try:
            # Check if profile exists
            existing_user = self.db.get_user(profile_name)
            if existing_user:
                return False, f"Profile '{profile_name}' already exists."

            # Create new user
            user_id = self.db.create_user(profile_name)
            if user_id is None:
                return False, "Failed to create profile in database."

            # Create sample chart for new users
            self._create_sample_chart_for_new_user()

            return True, f"Successfully created profile '{profile_name}'."
        except Exception as e:
            return False, f"Error creating profile: {e}"

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Get list of all profiles."""
        try:
            users = self.db.list_users()
            return users
        except Exception as e:
            print(f"Error listing profiles: {e}")
            return []

    def get_profile_stats(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific profile."""
        try:
            user = self.db.get_user(profile_name)
            if not user:
                return None

            stats = self.db.get_user_quiz_stats(user['id'])
            return stats
        except Exception as e:
            print(f"Error getting profile stats: {e}")
            return None

    # ============================================================================
    # QUIZ SERVICES
    # ============================================================================

    def run_hand_ranking_quiz(self, profile_name: str, count: int = 10,
                            difficulty: str = 'adaptive') -> Dict[str, Any]:
        """Run a hand ranking quiz session."""
        try:
            # Get user
            user = self.db.get_user(profile_name)
            if not user:
                return {'success': False, 'error': f"Profile '{profile_name}' not found."}

            # Initialize quiz
            quiz = HandRankingQuiz(
                difficulty=difficulty,
                db_path=self.db.db_path if difficulty == 'adaptive' else None,
                user_id=user['id'] if difficulty == 'adaptive' else None
            )

            # Run quiz
            result = quiz.run_interactive_quiz(count)

            # Save results
            session_id = self.db.create_quiz_session(
                user['id'], 'hand-ranking', result.correct_answers,
                result.total_questions, difficulty
            )

            if session_id is not None:
                # Save individual questions
                for i, (question, user_answer) in enumerate(zip(result.questions, result.user_answers)):
                    correct_idx = question.correct_answer
                    chosen_idx = user_answer
                    self.db.add_quiz_question(
                        session_id,
                        question.question_text,
                        str(correct_idx + 1),
                        str(chosen_idx + 1),
                        question.explanation
                    )

            return {
                'success': True,
                'correct': result.correct_answers,
                'total': result.total_questions,
                'score': result.correct_answers / result.total_questions * 100
            }

        except KeyboardInterrupt:
            return {'success': False, 'error': 'Quiz cancelled by user.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def run_pot_odds_quiz(self, profile_name: str, count: int = 10,
                         difficulty: str = 'adaptive') -> Dict[str, Any]:
        """Run a pot odds quiz session."""
        try:
            # Get user
            user = self.db.get_user(profile_name)
            if not user:
                return {'success': False, 'error': f"Profile '{profile_name}' not found."}

            # Initialize quiz
            quiz = PotOddsQuiz(
                difficulty=difficulty,
                db_path=self.db.db_path if difficulty == 'adaptive' else None,
                user_id=user['id'] if difficulty == 'adaptive' else None
            )

            # Run quiz
            result = quiz.run_interactive_quiz(count)

            # Save results
            session_id = self.db.create_quiz_session(
                user['id'], 'pot-odds', result.correct_answers,
                result.total_questions, difficulty
            )

            if session_id is not None:
                # Save individual questions
                for i, (question, user_answer) in enumerate(zip(result.questions, result.user_answers)):
                    correct_answer = "call" if question.should_call else "fold"
                    chosen_answer = "call" if user_answer else "fold"
                    self.db.add_quiz_question(
                        session_id,
                        question.question_text,
                        correct_answer,
                        chosen_answer,
                        question.explanation
                    )

            return {
                'success': True,
                'correct': result.correct_answers,
                'total': result.total_questions,
                'score': result.correct_answers / result.total_questions * 100
            }

        except KeyboardInterrupt:
            return {'success': False, 'error': 'Quiz cancelled by user.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # EQUITY CALCULATION SERVICES
    # ============================================================================

    def calculate_equity(self, hand1: str, hand2: str, board: Optional[str] = None,
                        iterations: int = 25000) -> Dict[str, Any]:
        """Calculate equity between two hands."""
        try:
            # Parse hands
            hand1_cards = parse_hand_string(hand1)
            hand2_cards = parse_hand_string(hand2)

            if len(hand1_cards) != 2 or len(hand2_cards) != 2:
                return {'success': False, 'error': 'Each hand must have exactly 2 cards.'}

            # Parse board if provided
            board_cards = []
            if board:
                board_cards = parse_hand_string(board)

            # Calculate equity
            calculator = EquityCalculator()
            result = calculator.calculate_equity(hand1_cards, hand2_cards, board_cards, iterations)

            return {
                'success': True,
                'hand1': hand1,
                'hand2': hand2,
                'board': board or '',
                'iterations': iterations,
                'equity': result.to_dict()
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error calculating equity: {str(e)}'
            }

    async def calculate_equity_async(self, hand1: str, hand2: str, board: Optional[str] = None,
                           iterations: int = 25000) -> Dict[str, Any]:
        """Calculate equity between two hands asynchronously."""
        try:
            # Parse hands
            hand1_cards = parse_hand_string(hand1)
            hand2_cards = parse_hand_string(hand2)

            if len(hand1_cards) != 2 or len(hand2_cards) != 2:
                return {'success': False, 'error': 'Each hand must have exactly 2 cards.'}

            # Parse board if provided
            board_cards = []
            if board:
                board_cards = parse_hand_string(board)

            # Calculate equity asynchronously
            calculator = EquityCalculator()
            result = await calculator.calculate_equity_async(hand1_cards, hand2_cards, board_cards, iterations)

            return {
                'success': True,
                'hand1': hand1,
                'hand2': hand2,
                'board': board or '',
                'iterations': iterations,
                'equity': result.to_dict()
            }

        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {e}'}

    # ============================================================================
    # SIMULATION SERVICES
    # ============================================================================

    def run_simulation(self, profile_name: str, ai_level: str = 'easy',
                      export_hand: Optional[str] = None, export_format: str = 'json') -> Dict[str, Any]:
        """Run a poker simulation against AI."""
        try:
            # Get user
            user = self.db.get_user(profile_name)
            if not user:
                return {'success': False, 'error': f"Profile '{profile_name}' not found."}

            # Initialize simulator
            simulator = PokerSimulator(ai_level=ai_level)

            # Run simulation
            result = simulator.simulate_hand()

            # Save to database
            session_id = self.db.create_sim_session(
                user['id'], 'texas-holdem', ai_level, result.winner
            )

            # Prepare result data
            simulation_data = {
                'winner': result.winner,
                'pot_size': result.pot_size,
                'player_cards': [str(c) for c in result.player_cards],
                'ai_cards': [str(c) for c in result.ai_cards],
                'board': [str(c) for c in result.board],
                'action_history': result.action_history,
                'final_hands': result.final_hands,
                'reasoning': result.reasoning
            }

            # Export hand history if requested
            if export_hand and session_id is not None:
                self.db.add_hand_history(session_id, json.dumps(simulation_data, indent=2))

                # Export to file using simulator's export functionality
                simulator.export_hand_history(export_hand, format=export_format)

            return {
                'success': True,
                'data': simulation_data,
                'session_id': session_id
            }

        except KeyboardInterrupt:
            return {'success': False, 'error': 'Simulation cancelled by user.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # CHART SERVICES
    # ============================================================================

    def list_charts(self) -> List[Dict[str, Any]]:
        """List all saved charts."""
        try:
            manager = ChartManager(self.db)
            charts = manager.list_charts()
            return charts
        except Exception as e:
            print(f"Error listing charts: {e}")
            return []

    def get_chart(self, chart_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific chart by name."""
        try:
            manager = ChartManager(self.db)
            actions = manager.load_chart_by_name(chart_name)

            if not actions:
                # Try to load sample chart
                if chart_name.lower() in ['sample', 'demo', 'test']:
                    actions = create_sample_range()
                    chart_name = "Sample GTO Chart"

            if actions:
                return {
                    'name': chart_name,
                    'actions': actions,
                    'hand_count': len(actions)
                }
            return None
        except Exception as e:
            print(f"Error loading chart: {e}")
            return None

    def save_chart(self, name: str, spot: str, actions: Dict[str, HandAction],
                  depth: int, position_hero: Optional[str] = None,
                  position_villain: Optional[str] = None) -> Tuple[bool, str]:
        """Save a chart to the database."""
        try:
            manager = ChartManager(self.db)
            chart_id = manager.save_chart(
                name, spot, actions, depth,
                position_hero or "",
                position_villain or ""
            )
            return True, f"Chart saved with ID: {chart_id}"
        except Exception as e:
            return False, f"Error saving chart: {e}"

    def export_chart(self, chart_name: str, format: str = 'txt') -> Tuple[bool, str]:
        """Export a chart to file."""
        try:
            manager = ChartManager(self.db)
            actions = manager.load_chart_by_name(chart_name)

            if not actions:
                return False, f"Chart '{chart_name}' not found."

            # Generate filename
            base_name = chart_name.lower().replace(' ', '_')
            output_path = f"{base_name}.{format}"

            if format == 'txt':
                matrix = HandMatrix(actions, chart_name)
                matrix.export_to_text(output_path)
            elif format == 'json':
                self._export_chart_to_json(chart_name, actions, output_path)
            elif format == 'csv':
                self._export_chart_to_csv(chart_name, actions, output_path)
            else:
                return False, f"Unsupported export format: {format}"

            return True, f"Chart exported to: {output_path}"
        except Exception as e:
            return False, f"Error exporting chart: {e}"

    def _export_chart_to_json(self, chart_name: str, actions: Dict[str, HandAction], filepath: str):
        """Export chart to JSON format."""
        export_data = {
            "name": chart_name,
            "export_format": "holdem-cli-v1",
            "export_timestamp": datetime.now().isoformat(),
            "total_hands": len(actions),
            "ranges": {
                hand: {
                    "action": action.action.value,
                    "frequency": action.frequency,
                    "ev": action.ev,
                    "notes": action.notes
                }
                for hand, action in actions.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def _export_chart_to_csv(self, chart_name: str, actions: Dict[str, HandAction], filepath: str):
        """Export chart to CSV format."""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Hand', 'Action', 'Frequency', 'EV', 'Notes'])

            for hand, action in sorted(actions.items()):
                writer.writerow([
                    hand,
                    action.action.value,
                    action.frequency,
                    action.ev or '',
                    action.notes
                ])

    def _create_sample_chart_for_new_user(self):
        """Create a sample chart for new users."""
        try:
            manager = ChartManager(self.db)
            sample_actions = create_sample_range()
            manager.save_chart(
                "Sample GTO Chart",
                "BTN vs BB 3-bet defense",
                sample_actions,
                100,
                "BTN",
                "BB"
            )
        except Exception as e:
            print(f"Warning: Could not create sample chart: {e}")


# Convenience function for one-off operations
def get_holdem_service() -> HoldemService:
    """Get a HoldemService instance for one-off operations."""
    return HoldemService()

