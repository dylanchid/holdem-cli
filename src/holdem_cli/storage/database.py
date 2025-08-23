"""Database schema and utilities for Holdem CLI."""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


def get_database_path() -> Path:
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
    
    return base_dir / 'holdem-cli' / 'holdem-cli.db'


class Database:
    """SQLite database manager for Holdem CLI."""
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize database connection."""
        self.db_path = db_path or get_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        # First, try to migrate existing database
        self._migrate_database()
        
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_hands_played INTEGER DEFAULT 0,
            total_winnings INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            correct_answer TEXT,
            chosen_answer TEXT,
            explanation TEXT,
            FOREIGN KEY(session_id) REFERENCES quiz_sessions(id)
        );
        
        CREATE TABLE IF NOT EXISTS sim_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            variant TEXT NOT NULL,
            ai_level TEXT,
            result TEXT,
            pot_size INTEGER DEFAULT 0,
            starting_chips INTEGER DEFAULT 1000,
            final_chips INTEGER DEFAULT 1000,
            hand_duration_seconds INTEGER DEFAULT 0,
            showdown_occurred BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS hand_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sim_session_id INTEGER NOT NULL,
            hand_data TEXT NOT NULL,  -- JSON data of the complete hand
            text TEXT,  -- Keep old column for compatibility
            FOREIGN KEY(sim_session_id) REFERENCES sim_sessions(id)
        );
        
        CREATE TABLE IF NOT EXISTS user_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stat_name TEXT NOT NULL,
            stat_value REAL NOT NULL,
            stat_category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS betting_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sim_session_id INTEGER NOT NULL,
            street TEXT NOT NULL,  -- preflop, flop, turn, river
            pot_before INTEGER DEFAULT 0,
            pot_after INTEGER DEFAULT 0,
            round_order INTEGER DEFAULT 0,
            FOREIGN KEY(sim_session_id) REFERENCES sim_sessions(id)
        );
        
        CREATE TABLE IF NOT EXISTS player_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            betting_round_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            action_type TEXT NOT NULL,  -- fold, call, raise, check, bet
            amount INTEGER DEFAULT 0,
            reasoning TEXT,
            action_order INTEGER DEFAULT 0,
            FOREIGN KEY(betting_round_id) REFERENCES betting_rounds(id)
        );

        CREATE TABLE IF NOT EXISTS charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spot TEXT NOT NULL,
            stack_depth INTEGER DEFAULT 100,
            position_hero TEXT,
            position_villain TEXT,
            data TEXT NOT NULL,  -- JSON data for chart ranges
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Critical indexes for performance optimization
        CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_type ON quiz_sessions(user_id, type);
        CREATE INDEX IF NOT EXISTS idx_quiz_sessions_created_at ON quiz_sessions(created_at);

        CREATE INDEX IF NOT EXISTS idx_quiz_questions_session_id ON quiz_questions(session_id);

        CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_id ON sim_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_created_at ON sim_sessions(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_sim_sessions_created_at ON sim_sessions(created_at);

        CREATE INDEX IF NOT EXISTS idx_hand_history_session_id ON hand_history(sim_session_id);

        CREATE INDEX IF NOT EXISTS idx_user_statistics_user_id ON user_statistics(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_statistics_user_name ON user_statistics(user_id, stat_name);

        CREATE INDEX IF NOT EXISTS idx_betting_rounds_session_id ON betting_rounds(sim_session_id);

        CREATE INDEX IF NOT EXISTS idx_player_actions_round_id ON player_actions(betting_round_id);

        CREATE INDEX IF NOT EXISTS idx_charts_name ON charts(name);
        """
        
        self.connection.executescript(schema)
        self.connection.commit()

        # Ensure indexes are created for existing databases
        self._create_indexes()

    def _create_indexes(self) -> None:
        """Create performance indexes for the database."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_type ON quiz_sessions(user_id, type)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_created_at ON quiz_sessions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_questions_session_id ON quiz_questions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_id ON sim_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_created_at ON sim_sessions(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sim_sessions_created_at ON sim_sessions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_hand_history_session_id ON hand_history(sim_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_statistics_user_id ON user_statistics(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_statistics_user_name ON user_statistics(user_id, stat_name)",
            "CREATE INDEX IF NOT EXISTS idx_betting_rounds_session_id ON betting_rounds(sim_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_player_actions_round_id ON player_actions(betting_round_id)",
            "CREATE INDEX IF NOT EXISTS idx_charts_name ON charts(name)"
        ]

        cursor = self.connection.cursor()
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                # Log warning but don't fail if index creation fails
                print(f"Warning: Could not create index: {e}")
        self.connection.commit()

    def optimize_database(self) -> None:
        """Optimize database performance by creating indexes."""
        """Create performance indexes for existing database."""
        print("🔧 Optimizing database with performance indexes...")
        self._create_indexes()
        print("✅ Database optimization complete")

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information including size and index status."""
        cursor = self.connection.cursor()

        # Get table sizes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        table_info = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_info[table_name] = count

        # Get index information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]

        return {
            'tables': table_info,
            'indexes': indexes,
            'total_indexes': len(indexes)
        }

    def _migrate_database(self) -> None:
        """Migrate existing database to new schema."""
        cursor = self.connection.cursor()
        
        try:
            # Check if we need to add new columns to existing tables
            
            # Check users table for new columns
            cursor.execute("PRAGMA table_info(users)")
            users_columns = [row[1] for row in cursor.fetchall()]
            
            if 'total_hands_played' not in users_columns:
                cursor.execute("ALTER TABLE users ADD COLUMN total_hands_played INTEGER DEFAULT 0")
            if 'total_winnings' not in users_columns:
                cursor.execute("ALTER TABLE users ADD COLUMN total_winnings INTEGER DEFAULT 0")
            
            # Check sim_sessions table for new columns
            cursor.execute("PRAGMA table_info(sim_sessions)")
            sim_columns = [row[1] for row in cursor.fetchall()]
            
            if 'pot_size' not in sim_columns:
                cursor.execute("ALTER TABLE sim_sessions ADD COLUMN pot_size INTEGER DEFAULT 0")
            if 'starting_chips' not in sim_columns:
                cursor.execute("ALTER TABLE sim_sessions ADD COLUMN starting_chips INTEGER DEFAULT 1000")
            if 'final_chips' not in sim_columns:
                cursor.execute("ALTER TABLE sim_sessions ADD COLUMN final_chips INTEGER DEFAULT 1000")
            if 'hand_duration_seconds' not in sim_columns:
                cursor.execute("ALTER TABLE sim_sessions ADD COLUMN hand_duration_seconds INTEGER DEFAULT 0")
            if 'showdown_occurred' not in sim_columns:
                cursor.execute("ALTER TABLE sim_sessions ADD COLUMN showdown_occurred BOOLEAN DEFAULT 0")
            
            # Check hand_history for new column
            cursor.execute("PRAGMA table_info(hand_history)")
            history_columns = [row[1] for row in cursor.fetchall()]
            
            if 'hand_data' not in history_columns:
                cursor.execute("ALTER TABLE hand_history ADD COLUMN hand_data TEXT")
            
            self.connection.commit()
        
        except Exception as e:
            # If migration fails, it's probably because tables don't exist yet
            # This is fine, they'll be created by the main schema
            pass
    
    def create_user(self, name: str) -> int:
        """Create a new user and return their ID."""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users (name) VALUES (?)",
            (name,)
        )
        self.connection.commit()
        result = cursor.lastrowid
        if result is None:
            raise RuntimeError("Failed to create user - no ID returned")
        return result
    
    def get_user(self, name: str) -> Optional[Dict[str, Any]]:
        """Get user by name."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def create_quiz_session(
        self,
        user_id: int,
        quiz_type: str,
        score: int,
        total: int,
        difficulty: Optional[str] = None
    ) -> int:
        """Create a new quiz session and return its ID."""
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO quiz_sessions (user_id, type, score, total, difficulty)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, quiz_type, score, total, difficulty)
        )
        self.connection.commit()
        result = cursor.lastrowid
        if result is None:
            raise RuntimeError("Failed to create quiz session - no ID returned")
        return result
    
    def add_quiz_question(
        self,
        session_id: int,
        prompt: str,
        correct_answer: str,
        chosen_answer: str,
        explanation: str
    ) -> None:
        """Add a quiz question to a session."""
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO quiz_questions 
               (session_id, prompt, correct_answer, chosen_answer, explanation)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, prompt, correct_answer, chosen_answer, explanation)
        )
        self.connection.commit()
    
    def get_user_quiz_stats(self, user_id: int) -> Dict[str, Any]:
        """Get quiz statistics for a user."""
        cursor = self.connection.cursor()
        
        # Overall stats
        cursor.execute(
            """SELECT 
                COUNT(*) as total_sessions,
                AVG(CAST(score AS FLOAT) / total * 100) as avg_accuracy,
                SUM(score) as total_correct,
                SUM(total) as total_questions
               FROM quiz_sessions 
               WHERE user_id = ?""",
            (user_id,)
        )
        overall = dict(cursor.fetchone())
        
        # Stats by type
        cursor.execute(
            """SELECT 
                type,
                COUNT(*) as sessions,
                AVG(CAST(score AS FLOAT) / total * 100) as avg_accuracy,
                MAX(CAST(score AS FLOAT) / total * 100) as best_accuracy
               FROM quiz_sessions 
               WHERE user_id = ?
               GROUP BY type""",
            (user_id,)
        )
        by_type = {row['type']: dict(row) for row in cursor.fetchall()}
        
        return {
            'overall': overall,
            'by_type': by_type
        }
    
    def create_sim_session(
        self,
        user_id: int,
        variant: str,
        ai_level: str,
        result: str,
        pot_size: int = 0,
        starting_chips: int = 1000,
        final_chips: int = 1000,
        hand_duration_seconds: int = 0,
        showdown_occurred: bool = False
    ) -> int:
        """Create a simulation session and return its ID."""
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO sim_sessions
               (user_id, variant, ai_level, result, pot_size, starting_chips,
                final_chips, hand_duration_seconds, showdown_occurred)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, variant, ai_level, result, pot_size, starting_chips,
             final_chips, hand_duration_seconds, showdown_occurred)
        )
        self.connection.commit()
        result_id = cursor.lastrowid
        if result_id is None:
            raise RuntimeError("Failed to create simulation session - no ID returned")
        return result_id
    
    def add_hand_history(self, sim_session_id: int, hand_data: str) -> None:
        """Add complete hand history data to a simulation session."""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO hand_history (sim_session_id, hand_data, text) VALUES (?, ?, ?)",
            (sim_session_id, hand_data, hand_data)  # Use same data for both columns
        )
        self.connection.commit()
    
    def save_betting_round(self, sim_session_id: int, street: str,
                          pot_before: int, pot_after: int, round_order: int) -> int:
        """Save a betting round and return its ID."""
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO betting_rounds
               (sim_session_id, street, pot_before, pot_after, round_order)
               VALUES (?, ?, ?, ?, ?)""",
            (sim_session_id, street, pot_before, pot_after, round_order)
        )
        self.connection.commit()
        result = cursor.lastrowid
        if result is None:
            raise RuntimeError("Failed to save betting round - no ID returned")
        return result
    
    def save_player_action(self, betting_round_id: int, player_name: str,
                          action_type: str, amount: int, reasoning: str, 
                          action_order: int) -> None:
        """Save a player action."""
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO player_actions 
               (betting_round_id, player_name, action_type, amount, reasoning, action_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (betting_round_id, player_name, action_type, amount, reasoning, action_order)
        )
        self.connection.commit()
    
    def update_user_statistics(self, user_id: int, stat_name: str, 
                              stat_value: float, stat_category: str = "general") -> None:
        """Update or insert user statistics."""
        cursor = self.connection.cursor()
        
        # Check if stat exists
        cursor.execute(
            "SELECT id FROM user_statistics WHERE user_id = ? AND stat_name = ?",
            (user_id, stat_name)
        )
        
        if cursor.fetchone():
            # Update existing stat
            cursor.execute(
                """UPDATE user_statistics 
                   SET stat_value = ?, last_updated = CURRENT_TIMESTAMP
                   WHERE user_id = ? AND stat_name = ?""",
                (stat_value, user_id, stat_name)
            )
        else:
            # Insert new stat
            cursor.execute(
                """INSERT INTO user_statistics 
                   (user_id, stat_name, stat_value, stat_category)
                   VALUES (?, ?, ?, ?)""",
                (user_id, stat_name, stat_value, stat_category)
            )
        
        self.connection.commit()
    
    def get_user_sim_stats(self, user_id: int) -> Dict[str, Any]:
        """Get simulation statistics for a user."""
        cursor = self.connection.cursor()
        
        # Overall simulation stats
        cursor.execute(
            """SELECT 
                COUNT(*) as total_hands,
                SUM(CASE WHEN result = 'Human' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'AI' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = 'Tie' THEN 1 ELSE 0 END) as ties,
                AVG(pot_size) as avg_pot_size,
                SUM(CASE WHEN showdown_occurred = 1 THEN 1 ELSE 0 END) as showdowns,
                AVG(hand_duration_seconds) as avg_hand_duration
               FROM sim_sessions 
               WHERE user_id = ?""",
            (user_id,)
        )
        overall = dict(cursor.fetchone())
        
        # Calculate win rate
        total_hands = overall['total_hands'] or 0
        if total_hands > 0:
            overall['win_rate'] = (overall['wins'] / total_hands) * 100
            overall['showdown_rate'] = (overall['showdowns'] / total_hands) * 100
        else:
            overall['win_rate'] = 0
            overall['showdown_rate'] = 0
        
        # Stats by AI level
        cursor.execute(
            """SELECT 
                ai_level,
                COUNT(*) as hands,
                SUM(CASE WHEN result = 'Human' THEN 1 ELSE 0 END) as wins,
                AVG(pot_size) as avg_pot_size
               FROM sim_sessions 
               WHERE user_id = ?
               GROUP BY ai_level""",
            (user_id,)
        )
        by_ai_level = {row['ai_level']: dict(row) for row in cursor.fetchall()}
        
        # Calculate win rates by AI level
        for level_stats in by_ai_level.values():
            if level_stats['hands'] > 0:
                level_stats['win_rate'] = (level_stats['wins'] / level_stats['hands']) * 100
            else:
                level_stats['win_rate'] = 0
        
        return {
            'overall': overall,
            'by_ai_level': by_ai_level
        }
    
    def get_user_combined_stats(self, user_id: int) -> Dict[str, Any]:
        """Get combined quiz and simulation statistics for a user."""
        quiz_stats = self.get_user_quiz_stats(user_id)
        sim_stats = self.get_user_sim_stats(user_id)
        
        return {
            'quiz': quiz_stats,
            'simulation': sim_stats,
            'user_id': user_id
        }
    
    def close(self) -> None:
        """Close database connection."""
        self.connection.close()


def init_database(db_path: Optional[Path] = None) -> Database:
    """Initialize and return a database instance."""
    return Database(db_path)
