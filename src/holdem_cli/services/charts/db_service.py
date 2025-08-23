"""
Database service layer for TUI operations.

This module provides a service layer for database operations,
abstracting data persistence from the UI components.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import sqlite3
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from ..widgets.matrix import HandAction, ChartAction
from ..services.chart_service import ChartMetadata
from ..core.cache import SmartCache


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: str = ":memory:"
    timeout: float = 5.0
    enable_foreign_keys: bool = True
    enable_wal_mode: bool = True


class DatabaseError(Exception):
    """Database operation error."""
    pass


class DatabaseService:
    """
    Service for database operations.

    This service handles all database interactions including:
    - Connection management
    - Chart persistence
    - Query execution
    - Migration management
    - Backup and restore
    """

    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self._connection: Optional[sqlite3.Connection] = None
        self._cache = SmartCache(max_size=100)  # Cache for database queries
        self._schema_version = 1

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        if self._connection is None:
            self._connect()

        try:
            yield self._connection
        except Exception as e:
            self._connection.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            # Don't close connection here as it's reused
            pass

    def _connect(self):
        """Establish database connection."""
        try:
            self._connection = sqlite3.connect(
                self.config.path,
                timeout=self.config.timeout
            )
            self._connection.row_factory = sqlite3.Row

            if self.config.enable_foreign_keys:
                self._connection.execute("PRAGMA foreign_keys = ON")

            if self.config.enable_wal_mode:
                self._connection.execute("PRAGMA journal_mode = WAL")

            self._initialize_schema()

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")

    def _initialize_schema(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Charts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS charts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version TEXT NOT NULL,
                    tags TEXT,  -- JSON array of tags
                    total_hands INTEGER DEFAULT 0,
                    metadata TEXT  -- JSON metadata
                )
            """)

            # Chart actions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chart_actions (
                    chart_id TEXT,
                    hand TEXT,
                    action TEXT NOT NULL,
                    frequency REAL DEFAULT 1.0,
                    ev REAL,
                    notes TEXT,
                    PRIMARY KEY (chart_id, hand),
                    FOREIGN KEY (chart_id) REFERENCES charts (id) ON DELETE CASCADE
                )
            """)

            # Statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chart_statistics (
                    chart_id TEXT PRIMARY KEY,
                    total_hands INTEGER,
                    action_distribution TEXT,  -- JSON
                    frequency_stats TEXT,      -- JSON
                    ev_stats TEXT,            -- JSON
                    hand_types TEXT,          -- JSON
                    updated_at TEXT,
                    FOREIGN KEY (chart_id) REFERENCES charts (id) ON DELETE CASCADE
                )
            """)

            # Sessions table for quiz/game tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,  -- 'quiz', 'game', 'training'
                    chart_id TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    score REAL,
                    metadata TEXT,  -- JSON additional data
                    FOREIGN KEY (chart_id) REFERENCES charts (id)
                )
            """)

            # User preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.commit()

    def save_chart(
        self,
        chart_id: str,
        metadata: ChartMetadata,
        actions: Dict[str, HandAction]
    ) -> bool:
        """
        Save a chart to the database.

        Args:
            chart_id: Chart ID
            metadata: Chart metadata
            actions: Chart actions

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")

                # Save chart metadata
                conn.execute("""
                    INSERT OR REPLACE INTO charts
                    (id, name, description, created_at, updated_at, version, tags, total_hands, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chart_id,
                    metadata.name,
                    metadata.description,
                    metadata.created_at.isoformat(),
                    metadata.updated_at.isoformat(),
                    metadata.version,
                    json.dumps(metadata.tags),
                    len(actions),
                    json.dumps(metadata.statistics)
                ))

                # Save chart actions
                for hand, action in actions.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO chart_actions
                        (chart_id, hand, action, frequency, ev, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        chart_id,
                        hand,
                        action.action.value,
                        action.frequency,
                        action.ev,
                        action.notes
                    ))

                # Save statistics
                if metadata.statistics:
                    conn.execute("""
                        INSERT OR REPLACE INTO chart_statistics
                        (chart_id, total_hands, action_distribution, frequency_stats,
                         ev_stats, hand_types, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chart_id,
                        metadata.statistics.get("total_hands", 0),
                        json.dumps(metadata.statistics.get("actions", {})),
                        json.dumps(metadata.statistics.get("frequency_stats", {})),
                        json.dumps(metadata.statistics.get("ev_stats", {})),
                        json.dumps(metadata.statistics.get("hand_types", {})),
                        datetime.now().isoformat()
                    ))

                conn.commit()

                # Clear cache
                self._cache.clear()

                return True

        except Exception as e:
            raise DatabaseError(f"Failed to save chart: {e}")

    def load_chart(self, chart_id: str) -> Tuple[Optional[ChartMetadata], Optional[Dict[str, HandAction]]]:
        """
        Load a chart from the database.

        Args:
            chart_id: Chart ID

        Returns:
            Tuple of (metadata, actions) or (None, None) if not found
        """
        cache_key = f"chart_{chart_id}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached["metadata"], cached["actions"]

        try:
            with self._get_connection() as conn:
                # Load metadata
                metadata_row = conn.execute("""
                    SELECT * FROM charts WHERE id = ?
                """, (chart_id,)).fetchone()

                if not metadata_row:
                    return None, None

                # Load actions
                actions_rows = conn.execute("""
                    SELECT * FROM chart_actions WHERE chart_id = ?
                """, (chart_id,)).fetchall()

                # Reconstruct metadata
                metadata = ChartMetadata(
                    id=metadata_row['id'],
                    name=metadata_row['name'],
                    description=metadata_row['description'] or "",
                    created_at=datetime.fromisoformat(metadata_row['created_at']),
                    updated_at=datetime.fromisoformat(metadata_row['updated_at']),
                    version=metadata_row['version'],
                    tags=json.loads(metadata_row['tags'] or '[]'),
                    statistics=json.loads(metadata_row['metadata'] or '{}')
                )

                # Reconstruct actions
                actions = {}
                for row in actions_rows:
                    actions[row['hand']] = HandAction(
                        action=ChartAction(row['action']),
                        frequency=row['frequency'],
                        ev=row['ev'],
                        notes=row['notes'] or ""
                    )

                # Cache result
                self._cache.set(cache_key, {
                    "metadata": metadata,
                    "actions": actions
                })

                return metadata, actions

        except Exception as e:
            raise DatabaseError(f"Failed to load chart: {e}")

    def list_charts(self, limit: int = 50, offset: int = 0) -> List[ChartMetadata]:
        """
        List charts in the database.

        Args:
            limit: Maximum number of charts to return
            offset: Number of charts to skip

        Returns:
            List of chart metadata
        """
        cache_key = f"charts_list_{limit}_{offset}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM charts
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset)).fetchall()

                charts = []
                for row in rows:
                    charts.append(ChartMetadata(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'] or "",
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        version=row['version'],
                        tags=json.loads(row['tags'] or '[]'),
                        statistics=json.loads(row['metadata'] or '{}')
                    ))

                # Cache result
                self._cache.set(cache_key, charts)

                return charts

        except Exception as e:
            raise DatabaseError(f"Failed to list charts: {e}")

    def delete_chart(self, chart_id: str) -> bool:
        """
        Delete a chart from the database.

        Args:
            chart_id: Chart ID

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                # Delete chart (cascade will handle related data)
                result = conn.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
                conn.commit()

                if result.rowcount > 0:
                    # Clear cache
                    self._cache.clear()
                    return True

                return False

        except Exception as e:
            raise DatabaseError(f"Failed to delete chart: {e}")

    def search_charts(self, query: str, limit: int = 20) -> List[ChartMetadata]:
        """
        Search for charts by name or description.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching chart metadata
        """
        try:
            with self._get_connection() as conn:
                # Simple LIKE search - could be enhanced with FTS
                rows = conn.execute("""
                    SELECT * FROM charts
                    WHERE name LIKE ? OR description LIKE ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit)).fetchall()

                charts = []
                for row in rows:
                    charts.append(ChartMetadata(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'] or "",
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        version=row['version'],
                        tags=json.loads(row['tags'] or '[]'),
                        statistics=json.loads(row['metadata'] or '{}')
                    ))

                return charts

        except Exception as e:
            raise DatabaseError(f"Failed to search charts: {e}")

    def save_session(
        self,
        session_id: str,
        session_type: str,
        chart_id: Optional[str],
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a session record.

        Args:
            session_id: Session ID
            session_type: Type of session ('quiz', 'game', 'training')
            chart_id: Associated chart ID
            score: Session score
            metadata: Additional session data

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions
                    (id, type, chart_id, started_at, completed_at, score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    session_type,
                    chart_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    score,
                    json.dumps(metadata or {})
                ))
                conn.commit()
                return True

        except Exception as e:
            raise DatabaseError(f"Failed to save session: {e}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get user preference.

        Args:
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value
        """
        cache_key = f"pref_{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            with self._get_connection() as conn:
                row = conn.execute("""
                    SELECT value FROM preferences WHERE key = ?
                """, (key,)).fetchone()

                if row:
                    value = json.loads(row['value'])
                    self._cache.set(cache_key, value)
                    return value
                else:
                    return default

        except Exception as e:
            raise DatabaseError(f"Failed to get preference: {e}")

    def set_preference(self, key: str, value: Any) -> bool:
        """
        Set user preference.

        Args:
            key: Preference key
            value: Preference value

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO preferences (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (
                    key,
                    json.dumps(value),
                    datetime.now().isoformat()
                ))
                conn.commit()

                # Update cache
                self._cache.set(f"pref_{key}", value)
                return True

        except Exception as e:
            raise DatabaseError(f"Failed to set preference: {e}")

    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for backup file

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                # Create backup using SQLite's backup API
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
                return True

        except Exception as e:
            raise DatabaseError(f"Failed to create backup: {e}")

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            with self._get_connection() as conn:
                stats = {}

                # Chart statistics
                chart_count = conn.execute("SELECT COUNT(*) FROM charts").fetchone()[0]
                stats['total_charts'] = chart_count

                # Action statistics
                action_count = conn.execute("SELECT COUNT(*) FROM chart_actions").fetchone()[0]
                stats['total_actions'] = action_count

                # Session statistics
                session_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
                stats['total_sessions'] = session_count

                # Database size
                if self.config.path != ":memory:":
                    db_path = Path(self.config.path)
                    if db_path.exists():
                        stats['database_size_bytes'] = db_path.stat().st_size
                    else:
                        stats['database_size_bytes'] = 0

                return stats

        except Exception as e:
            raise DatabaseError(f"Failed to get database stats: {e}")

    def optimize_database(self) -> bool:
        """
        Optimize database performance.

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                # Run optimization commands
                conn.execute("VACUUM")
                conn.execute("PRAGMA optimize")
                conn.commit()
                return True

        except Exception as e:
            raise DatabaseError(f"Failed to optimize database: {e}")

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._cache.clear()


# Global service instance
_db_service: Optional[DatabaseService] = None


def get_database_service(config: DatabaseConfig = None) -> DatabaseService:
    """Get or create the global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(config)
    return _db_service


def reset_database_service():
    """Reset the global database service instance."""
    global _db_service
    if _db_service:
        _db_service.close()
    _db_service = None
