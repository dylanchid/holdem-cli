"""
Standardized data models for Holdem CLI.

This module provides consistent data structures used across all application modules,
ensuring type safety and interface compatibility.
"""

from .base import BaseModel, TimestampMixin, Identifiable
from .poker import Card, Hand, Deck, PokerHand, HandStrength, HandRank, Suit, Rank
from .quiz import QuizQuestion, QuizResult, QuizSession, QuizAnswer, LearningProgress

__all__ = [
    'BaseModel', 'TimestampMixin', 'Identifiable',
    'Card', 'Hand', 'Deck', 'PokerHand', 'HandStrength', 'HandRank', 'Suit', 'Rank',
    'QuizQuestion', 'QuizResult', 'QuizSession', 'QuizAnswer', 'LearningProgress'
]
