"""
Optimized SQLite database manager for Holdem CLI.

This module provides performance-optimized database operations
with caching, batch processing, and query optimization.
"""

import sqlite3
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from functools import lru_cache
import threading

from ..utils.logging_utils import get_logger


class QueryCache:
    """Thread-safe query result cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """Initialize cache with max size and TTL."""
        self._cache = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any) -> None:
        """Set cached value with current timestamp."""
        with self._lock:
            if len(self._cache) >= self._max_size:
                # Remove oldest entries (simple FIFO)
                oldest_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: self._cache[k][1]
                )[:len(self._cache) // 4]  # Remove 25% oldest

                for old_key in oldest_keys:
                    del self._cache[old_key]

            self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'ttl_seconds': self._ttl
            }


class OptimizedDatabase:
    """Performance-optimized SQLite database manager."""

    def __init__(self, db_path: Optional[Path] = None, enable_cache: bool = True):
        """Initialize optimized database connection."""
        self.db_path = db_path or self._get_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.enable_cache = enable_cache
        self._cache = QueryCache() if enable_cache else None
        self._logger = get_logger()

        # Connection management
        self._connection = None
        self._connection_lock = threading.Lock()

        # Performance tracking
        self._query_stats = {'count': 0, 'total_time': 0.0, 'cache_hits': 0}

        self._ensure_connection()
        self._create_tables()
        self._create_optimized_indexes()

    def _get_database_path(self) -> Path:
        """Get the standard database path based on OS."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', '~')).expanduser()
        elif os.name == 'posix':
            if os.uname().sysname == 'Darwin':  # macOS
                base_dir = Path('~/Library/Application Support').expanduser()
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_DATA_HOME', '~/.local/share')).expanduser()
        else:
            base_dir = Path('~/.local/share').expanduser()

        return base_dir / 'holdem-cli' / 'holdem-cli-optimized.db'

    def _ensure_connection(self) -> None:
        """Ensure database connection exists and is valid."""
        with self._connection_lock:
            if self._connection is None:
                self._connection = sqlite3.connect(str(self.db_path))
                self._connection.row_factory = sqlite3.Row
                # Enable WAL mode for better concurrency
                self._connection.execute('PRAGMA journal_mode=WAL')
                # Enable foreign keys
                self._connection.execute('PRAGMA foreign_keys=ON')
                # Set busy timeout
                self._connection.execute('PRAGMA busy_timeout=30000')

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        schema = """
        -- Users table with additional performance fields
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_hands_played INTEGER DEFAULT 0,
            total_winnings INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preferences TEXT DEFAULT '{}'  -- JSON field for user preferences
        );

        -- Quiz sessions with performance optimizations
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration_seconds INTEGER DEFAULT 0,
            questions_asked INTEGER DEFAULT 0
        );

        -- Quiz questions with optimized storage
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            hand TEXT NOT NULL,  -- Store hand instead of full prompt
            correct_answer TEXT,
            chosen_answer TEXT,
            explanation TEXT,
            is_correct BOOLEAN GENERATED ALWAYS AS (correct_answer = chosen_answer) STORED
        );

        -- Simulation sessions
        CREATE TABLE IF NOT EXISTS sim_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            variant TEXT NOT NULL,
            ai_level TEXT,
            result TEXT,
            pot_size INTEGER DEFAULT 0,
            starting_chips INTEGER DEFAULT 1000,
            final_chips INTEGER DEFAULT 1000,
            hand_duration_seconds INTEGER DEFAULT 0,
            showdown_occurred BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Hand history with compressed storage
        CREATE TABLE IF NOT EXISTS hand_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sim_session_id INTEGER NOT NULL REFERENCES sim_sessions(id) ON DELETE CASCADE,
            hand_data TEXT NOT NULL,  -- JSON data
            compressed BOOLEAN DEFAULT 0
        );

        -- User statistics with efficient lookups
        CREATE TABLE IF NOT EXISTS user_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stat_name TEXT NOT NULL,
            stat_value REAL NOT NULL,
            stat_category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, stat_name)
        );
        """

        cursor = self._connection.cursor()
        cursor.executescript(schema)
        self._connection.commit()

    def _create_optimized_indexes(self) -> None:
        """Create performance-optimized indexes."""
        indexes = [
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_name ON users(name)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",

            # Quiz session indexes - optimized for common queries
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_date ON quiz_sessions(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_type_date ON quiz_sessions(type, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_difficulty ON quiz_sessions(difficulty)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_performance ON quiz_sessions(score, total)",

            # Quiz questions - optimized for session-based queries
            "CREATE INDEX IF NOT EXISTS idx_quiz_questions_session ON quiz_questions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_questions_correct ON quiz_questions(is_correct)",

            # Simulation indexes
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_date ON sim_sessions(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_result ON sim_sessions(result)",
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_ai_level ON sim_sessions(ai_level)",

            # Statistics indexes
            "CREATE INDEX IF NOT EXISTS idx_user_statistics_user_name ON user_statistics(user_id, stat_name)",
            "CREATE INDEX IF NOT EXISTS idx_user_statistics_category ON user_statistics(stat_category)",
            "CREATE INDEX IF NOT EXISTS idx_user_statistics_updated ON user_statistics(last_updated)",

            # Composite indexes for complex queries
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_type_date ON quiz_sessions(user_id, type, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_ai_date ON sim_sessions(user_id, ai_level, created_at)",
        ]

        cursor = self._connection.cursor()
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                self._logger.warning(f"Could not create index: {e}")

        self._connection.commit()
        self._logger.info("Optimized database indexes created")

    def _execute_query(self, query: str, params: Tuple = (), cache_key: Optional[str] = None) -> List[Dict]:
        """Execute query with caching and performance tracking."""
        start_time = time.time()

        # Check cache first
        if cache_key and self._cache:
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                self._query_stats['cache_hits'] += 1
                self._query_stats['count'] += 1
                self._query_stats['total_time'] += time.time() - start_time
                return cached_result

        # Execute query
        self._ensure_connection()
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to dict format
        result = [dict(row) for row in rows]

        # Cache result if cache key provided
        if cache_key and self._cache:
            self._cache.set(cache_key, result)

        # Update stats
        self._query_stats['count'] += 1
        self._query_stats['total_time'] += time.time() - start_time

        return result

    def _execute_write(self, query: str, params: Tuple = ()) -> int:
        """Execute write operation with transaction handling."""
        start_time = time.time()

        self._ensure_connection()
        cursor = self._connection.cursor()

        try:
            cursor.execute(query, params)
            self._connection.commit()

            # Clear relevant cache entries
            if self._cache:
                self._cache.clear()  # Simple approach - clear all cache on writes

            # Update stats
            self._query_stats['count'] += 1
            self._query_stats['total_time'] += time.time() - start_time

            return cursor.lastrowid or 0

        except Exception as e:
            self._connection.rollback()
            raise e

    # Batch operations for better performance
    def batch_create_quiz_questions(self, questions_data: List[Dict[str, Any]]) -> None:
        """Batch insert multiple quiz questions efficiently."""
        if not questions_data:
            return

        query = """
        INSERT INTO quiz_questions (session_id, hand, correct_answer, chosen_answer, explanation)
        VALUES (?, ?, ?, ?, ?)
        """

        # Prepare data for batch insert
        batch_data = []
        for q_data in questions_data:
            batch_data.append((
                q_data['session_id'],
                q_data['hand'],
                q_data['correct_answer'],
                q_data['chosen_answer'],
                q_data['explanation']
            ))

        self._ensure_connection()
        cursor = self._connection.cursor()

        try:
            cursor.executemany(query, batch_data)
            self._connection.commit()

            if self._cache:
                self._cache.clear()

            self._logger.info(f"Batch inserted {len(batch_data)} quiz questions")

        except Exception as e:
            self._connection.rollback()
            raise e

    def get_user_quiz_stats_optimized(self, user_id: int) -> Dict[str, Any]:
        """Get user quiz statistics with optimized queries."""
        cache_key = f"user_quiz_stats_{user_id}"

        # Use a single optimized query instead of multiple queries
        query = """
        SELECT
            COUNT(*) as total_sessions,
            AVG(CAST(score AS FLOAT) / total * 100) as avg_accuracy,
            SUM(score) as total_correct,
            SUM(total) as total_questions,
            type,
            COUNT(*) as type_sessions,
            AVG(CAST(score AS FLOAT) / total * 100) as type_avg_accuracy
        FROM quiz_sessions
        WHERE user_id = ?
        GROUP BY GROUPING SETS (
            (),  -- Overall stats
            (type)  -- By type stats
        )
        """

        rows = self._execute_query(query, (user_id,), cache_key)

        # Process results
        overall = {}
        by_type = {}

        for row in rows:
            if row['type'] is None:
                # Overall stats
                overall = {
                    'total_sessions': row['total_sessions'],
                    'avg_accuracy': row['avg_accuracy'] or 0,
                    'total_questions': row['total_questions'] or 0
                }
            else:
                # Type-specific stats
                by_type[row['type']] = {
                    'sessions': row['type_sessions'],
                    'avg_accuracy': row['type_avg_accuracy'] or 0
                }

        return {
            'overall': overall,
            'by_type': by_type
        }

    def get_user_combined_stats_optimized(self, user_id: int) -> Dict[str, Any]:
        """Get combined user statistics with single query optimization."""
        # Single query to get both quiz and simulation stats
        quiz_query = """
        SELECT
            'quiz' as category,
            COUNT(*) as total_sessions,
            AVG(CAST(score AS FLOAT) / total * 100) as avg_accuracy,
            SUM(total) as total_questions
        FROM quiz_sessions
        WHERE user_id = ?
        """

        sim_query = """
        SELECT
            'sim' as category,
            COUNT(*) as total_hands,
            SUM(CASE WHEN result = 'Human' THEN 1 ELSE 0 END) as wins,
            AVG(pot_size) as avg_pot_size
        FROM sim_sessions
        WHERE user_id = ?
        """

        quiz_stats = self._execute_query(quiz_query, (user_id,))
        sim_stats = self._execute_query(sim_query, (user_id,))

        return {
            'quiz': quiz_stats[0] if quiz_stats else {},
            'simulation': sim_stats[0] if sim_stats else {},
            'user_id': user_id
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        return {
            'query_stats': self._query_stats.copy(),
            'cache_stats': self._cache.stats() if self._cache else None,
            'avg_query_time': (
                self._query_stats['total_time'] / self._query_stats['count']
                if self._query_stats['count'] > 0 else 0
            ),
            'cache_hit_rate': (
                self._query_stats['cache_hits'] / self._query_stats['count'] * 100
                if self._query_stats['count'] > 0 else 0
            )
        }

    def optimize_database(self) -> None:
        """Run database optimization operations."""
        self._ensure_connection()
        cursor = self._connection.cursor()

        # Run VACUUM to reclaim space
        cursor.execute("VACUUM")

        # Run ANALYZE to update query planner statistics
        cursor.execute("ANALYZE")

        # Clear cache to ensure fresh data
        if self._cache:
            self._cache.clear()

        self._connection.commit()
        self._logger.info("Database optimization completed")

    def close(self) -> None:
        """Close database connection and cleanup."""
        with self._connection_lock:
            if self._connection:
                self._connection.close()
                self._connection = None

        # Log final performance stats
        stats = self.get_performance_stats()
        self._logger.info(f"Database connection closed. Final stats: {stats}")


# Maintain backward compatibility
def init_database(db_path: Optional[Path] = None) -> OptimizedDatabase:
    """Initialize and return an optimized database instance."""
    return OptimizedDatabase(db_path)
