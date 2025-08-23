"""
Input validation utilities for Holdem CLI.

This module provides centralized input validation to ensure
security and data integrity across all user inputs.
"""

import re
from typing import List, Optional, Union, Dict, Any
from pathlib import Path

from ..utils.logging_utils import get_logger


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Centralized input validation for the application."""

    # Regex patterns for validation
    CARD_PATTERN = re.compile(r'^[2-9TJQKA][cdhs]$', re.IGNORECASE)
    HAND_PATTERN = re.compile(r'^([2-9TJQKA][cdhs]\s*){2,}$', re.IGNORECASE)
    PROFILE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
    CHART_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\s-]{1,100}$')
    FILE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]{1,260}$')
    NUMERIC_PATTERN = re.compile(r'^\d+$')

    # Valid ranges
    VALID_DIFFICULTIES = ['easy', 'medium', 'hard', 'adaptive']
    VALID_AI_LEVELS = ['easy', 'medium', 'hard']
    VALID_POSITIONS = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']
    VALID_SCENARIOS = ['open_raise', '3bet', '4bet', 'vs_steal', 'squeeze', 'cold_call']
    VALID_STACK_DEPTHS = [20, 50, 100, 200]

    @classmethod
    def validate_card_string(cls, card_str: str) -> bool:
        """Validate a single card string (e.g., 'As', 'Kh')."""
        if not isinstance(card_str, str):
            return False

        card_str = card_str.strip()
        return bool(cls.CARD_PATTERN.match(card_str))

    @classmethod
    def validate_hand_string(cls, hand_str: str) -> bool:
        """Validate a hand string (e.g., 'AsKs' or 'As Ks')."""
        if not isinstance(hand_str, str):
            return False

        hand_str = hand_str.replace(' ', '').strip()
        if len(hand_str) < 4 or len(hand_str) > 6:  # 2-3 cards
            return False

        return bool(cls.HAND_PATTERN.match(hand_str))

    @classmethod
    def validate_profile_name(cls, name: str) -> bool:
        """Validate a profile name."""
        if not isinstance(name, str):
            return False

        return bool(cls.PROFILE_NAME_PATTERN.match(name))

    @classmethod
    def validate_chart_name(cls, name: str) -> bool:
        """Validate a chart name."""
        if not isinstance(name, str):
            return False

        return bool(cls.CHART_NAME_PATTERN.match(name))

    @classmethod
    def validate_file_path(cls, path: str) -> bool:
        """Validate a file path."""
        if not isinstance(path, str):
            return False

        # Basic path validation
        if '..' in path or path.startswith('/'):
            return False

        return bool(cls.FILE_PATH_PATTERN.match(path))

    @classmethod
    def validate_numeric_input(cls, value: str, min_val: int = 0, max_val: int = 1000000) -> bool:
        """Validate numeric input within a range."""
        if not isinstance(value, str):
            return False

        if not cls.NUMERIC_PATTERN.match(value):
            return False

        try:
            num = int(value)
            return min_val <= num <= max_val
        except ValueError:
            return False

    @classmethod
    def validate_difficulty(cls, difficulty: str) -> bool:
        """Validate difficulty level."""
        return difficulty in cls.VALID_DIFFICULTIES

    @classmethod
    def validate_ai_level(cls, ai_level: str) -> bool:
        """Validate AI difficulty level."""
        return ai_level in cls.VALID_AI_LEVELS

    @classmethod
    def validate_position(cls, position: str) -> bool:
        """Validate poker position."""
        return position.upper() in cls.VALID_POSITIONS

    @classmethod
    def validate_scenario(cls, scenario: str) -> bool:
        """Validate poker scenario."""
        return scenario in cls.VALID_SCENARIOS

    @classmethod
    def validate_stack_depth(cls, depth: int) -> bool:
        """Validate stack depth."""
        return depth in cls.VALID_STACK_DEPTHS

    @classmethod
    def validate_positive_integer(cls, value: Union[str, int], max_val: int = 1000000) -> bool:
        """Validate a positive integer."""
        try:
            if isinstance(value, str):
                num = int(value)
            else:
                num = value
            return 0 < num <= max_val
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_range(cls, value: Union[str, int], min_val: int = 0, max_val: int = 1000000) -> bool:
        """Validate a value is within a specified range."""
        try:
            if isinstance(value, str):
                num = int(value)
            else:
                num = value
            return min_val <= num <= max_val
        except (ValueError, TypeError):
            return False

    @classmethod
    def sanitize_input(cls, input_str: str, max_length: int = 1000) -> str:
        """Sanitize user input by removing potentially harmful characters."""
        if not isinstance(input_str, str):
            raise ValidationError("Input must be a string")

        # Remove null bytes and other control characters
        sanitized = input_str.replace('\x00', '')

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @classmethod
    def validate_and_sanitize_file_path(cls, path: str) -> Path:
        """Validate and sanitize a file path."""
        if not cls.validate_file_path(path):
            raise ValidationError(f"Invalid file path: {path}")

        sanitized = cls.sanitize_input(path, 260)
        return Path(sanitized)

    @classmethod
    def validate_poker_cards(cls, cards: List[str]) -> List[str]:
        """Validate a list of poker card strings."""
        validated_cards = []

        for card in cards:
            if not cls.validate_card_string(card):
                raise ValidationError(f"Invalid card: {card}")
            validated_cards.append(card.upper())

        return validated_cards

    @classmethod
    def validate_user_input(cls, input_type: str, value: Any) -> Any:
        """Generic input validation dispatcher."""
        validators = {
            'profile_name': cls.validate_profile_name,
            'chart_name': cls.validate_chart_name,
            'file_path': cls.validate_file_path,
            'difficulty': cls.validate_difficulty,
            'ai_level': cls.validate_ai_level,
            'position': cls.validate_position,
            'scenario': cls.validate_scenario,
            'card_string': cls.validate_card_string,
            'hand_string': cls.validate_hand_string,
        }

        if input_type not in validators:
            raise ValidationError(f"Unknown input type: {input_type}")

        if not validators[input_type](value):
            raise ValidationError(f"Invalid {input_type}: {value}")

        return value


def validate_with_logging(func_name: str, validation_func, *args, **kwargs):
    """Wrapper to validate input and log validation failures."""
    try:
        return validation_func(*args, **kwargs)
    except ValidationError as e:
        get_logger().warning(f"Validation failed in {func_name}: {e}")
        raise
    except Exception as e:
        get_logger().error(f"Unexpected error during validation in {func_name}: {e}")
        raise ValidationError(f"Validation error in {func_name}: {e}")


# Convenience functions with logging
def validate_profile_name_safe(name: str) -> str:
    """Safely validate a profile name with logging."""
    return validate_with_logging("validate_profile_name", InputValidator.validate_profile_name, name)


def validate_card_string_safe(card: str) -> bool:
    """Safely validate a card string with logging."""
    return validate_with_logging("validate_card_string", InputValidator.validate_card_string, card)


def validate_hand_string_safe(hand: str) -> bool:
    """Safely validate a hand string with logging."""
    return validate_with_logging("validate_hand_string", InputValidator.validate_hand_string, hand)
