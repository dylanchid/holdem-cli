"""
Centralized random number generation utilities for Holdem CLI.

This module provides secure, thread-safe random number generation
to ensure consistent behavior across all poker simulations and quizzes.
"""

import random
import secrets
from typing import Optional
from threading import Lock


class SecureRandom:
    """
    Thread-safe, secure random number generator for poker applications.

    This class provides a centralized way to generate random numbers
    that is both secure and deterministic when needed for testing.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize the random number generator.

        Args:
            seed: Optional seed for deterministic behavior (mainly for testing).
                  If None, uses cryptographically secure random seeding.
        """
        self._lock = Lock()

        if seed is not None:
            # Deterministic mode for testing
            self._random = random.Random(seed)
            self._is_deterministic = True
        else:
            # Secure mode for production
            # Use cryptographically secure seed
            secure_seed = secrets.randbits(128)
            self._random = random.Random(secure_seed)
            self._is_deterministic = False

    def seed(self, seed: int) -> None:
        """Set a new seed for deterministic behavior.

        Args:
            seed: The seed value to use
        """
        with self._lock:
            self._random.seed(seed)
            self._is_deterministic = True

    def random(self) -> float:
        """Generate a random float between 0.0 and 1.0."""
        with self._lock:
            return self._random.random()

    def randint(self, a: int, b: int) -> int:
        """Generate a random integer between a and b (inclusive)."""
        with self._lock:
            return self._random.randint(a, b)

    def choice(self, seq):
        """Choose a random element from a sequence."""
        with self._lock:
            return self._random.choice(seq)

    def shuffle(self, seq) -> None:
        """Shuffle a sequence in place."""
        with self._lock:
            self._random.shuffle(seq)

    def sample(self, population, k: int):
        """Choose k unique random elements from a population."""
        with self._lock:
            return self._random.sample(population, k)

    def is_deterministic(self) -> bool:
        """Check if the generator is in deterministic mode."""
        return self._is_deterministic

    def reseed_securely(self) -> None:
        """Reseed with a cryptographically secure random value."""
        with self._lock:
            secure_seed = secrets.randbits(128)
            self._random.seed(secure_seed)
            self._is_deterministic = False


# Global instance for application-wide use
_global_random = SecureRandom()


def get_global_random() -> SecureRandom:
    """Get the global random number generator instance."""
    return _global_random


def set_global_seed(seed: int) -> None:
    """Set the global random seed for deterministic behavior."""
    _global_random.seed(seed)


def is_deterministic_mode() -> bool:
    """Check if the global generator is in deterministic mode."""
    return _global_random.is_deterministic()


def reseed_securely() -> None:
    """Reseed the global generator with a secure random value."""
    _global_random.reseed_securely()


# Convenience functions that mirror the global random interface
def random() -> float:
    """Generate a random float using the global generator."""
    return _global_random.random()


def randint(a: int, b: int) -> int:
    """Generate a random integer using the global generator."""
    return _global_random.randint(a, b)


def choice(seq):
    """Choose a random element using the global generator."""
    return _global_random.choice(seq)


def shuffle(seq) -> None:
    """Shuffle a sequence using the global generator."""
    _global_random.shuffle(seq)


def sample(population, k: int):
    """Choose k unique random elements using the global generator."""
    return _global_random.sample(population, k)
