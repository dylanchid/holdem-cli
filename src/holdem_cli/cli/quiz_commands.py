# src/holdem_cli/cli/quiz_commands.py
"""Quiz-related CLI commands."""

import click
from holdem_cli.storage import init_database


@click.group()
def quiz() -> None:
    """Quiz commands for poker training."""
    pass


@quiz.command('hand-ranking')
@click.option('--count', default=10, help='Number of questions')
@click.option('--profile', default='default', help='Profile to use')
@click.option('--difficulty', default='adaptive',
              type=click.Choice(['adaptive', 'easy', 'medium', 'hard']),
              help='Quiz difficulty (adaptive uses user performance)')
def quiz_hand_ranking(count: int, profile: str, difficulty: str) -> None:
    """Quiz on poker hand rankings."""
    from holdem_cli.quiz.hand_ranking import HandRankingQuiz

    # Initialize database and check user
    db = init_database()
    user = db.get_user(profile)
    if not user:
        click.echo(f"Profile '{profile}' not found. Run 'holdem init --profile {profile}' first.")
        db.close()
        return

    try:
        # Run the quiz with adaptive difficulty support
        quiz = HandRankingQuiz(
            difficulty=difficulty,
            db_path=db.db_path if difficulty == 'adaptive' else None,
            user_id=user['id'] if difficulty == 'adaptive' else None
        )
        result = quiz.run_interactive_quiz(count)

        # Save results to database
        session_id = db.create_quiz_session(
            user['id'], 'hand-ranking',
            result.correct_answers, result.total_questions, difficulty
        )

        if session_id is not None:
            # Save individual questions
            for i, (question, user_answer) in enumerate(zip(result.questions, result.user_answers)):
                correct_idx = question.correct_answer
                chosen_idx = user_answer

                db.add_quiz_question(
                    session_id,
                    question.question_text,
                    str(correct_idx + 1),  # Convert to 1-based for storage
                    str(chosen_idx + 1),   # Convert to 1-based for storage
                    question.explanation
                )
        else:
            click.echo("Warning: Could not create quiz session in database.")

        click.echo(f"\nQuiz results saved to profile '{profile}'.")

    except KeyboardInterrupt:
        click.echo("\nQuiz cancelled.")
    except Exception as e:
        click.echo(f"Error running quiz: {e}")
    finally:
        db.close()


@quiz.command('pot-odds')
@click.option('--count', default=10, help='Number of questions')
@click.option('--profile', default='default', help='Profile to use')
@click.option('--difficulty', default='adaptive',
              type=click.Choice(['adaptive', 'easy', 'medium', 'hard']),
              help='Quiz difficulty (adaptive uses user performance)')
def quiz_pot_odds(count: int, profile: str, difficulty: str) -> None:
    """Quiz on pot odds calculations."""
    from holdem_cli.quiz.pot_odds import PotOddsQuiz

    # Initialize database and check user
    db = init_database()
    user = db.get_user(profile)
    if not user:
        click.echo(f"Profile '{profile}' not found. Run 'holdem init --profile {profile}' first.")
        db.close()
        return

    try:
        # Run the quiz with adaptive difficulty support
        quiz = PotOddsQuiz(
            difficulty=difficulty,
            db_path=db.db_path if difficulty == 'adaptive' else None,
            user_id=user['id'] if difficulty == 'adaptive' else None
        )
        result = quiz.run_interactive_quiz(count)

        # Save results to database
        session_id = db.create_quiz_session(
            user['id'], 'pot-odds',
            result.correct_answers, result.total_questions, difficulty
        )

        if session_id is not None:
            # Save individual questions
            for i, (question, user_answer) in enumerate(zip(result.questions, result.user_answers)):
                correct_answer = "call" if question.should_call else "fold"
                chosen_answer = "call" if user_answer else "fold"

                db.add_quiz_question(
                    session_id,
                    question.question_text,
                    correct_answer,
                    chosen_answer,
                    question.explanation
                )
        else:
            click.echo("Warning: Could not create quiz session in database.")

        click.echo(f"\nQuiz results saved to profile '{profile}'.")

    except KeyboardInterrupt:
        click.echo("\nQuiz cancelled.")
    except Exception as e:
        click.echo(f"Error running quiz: {e}")
    finally:
        db.close()
