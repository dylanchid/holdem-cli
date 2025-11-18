"""
Chart repository for unified chart data access.

This module provides a single source of truth for chart data conversion
and database operations, eliminating duplication across the codebase.
"""

import json
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass

from holdem_cli.types import HandAction, ChartAction
from holdem_cli.storage import Database
from holdem_cli.utils.error_handling import DatabaseError, log_error_and_continue
from holdem_cli.utils.logging_utils import get_logger


@dataclass
class ChartInfo:
    """Chart information and metadata."""
    id: int
    name: str
    spot: str
    stack_depth: int
    position_hero: str
    position_villain: str
    created_at: datetime


class ChartRepository:
    """
    Repository for chart data operations.

    Provides unified methods for saving, loading, and listing charts,
    with consistent data conversion between domain objects and database format.
    """

    def __init__(self, db: Database):
        """Initialize repository with database connection."""
        self.db = db
        self._logger = get_logger()

    # ========================================================================
    # Data Conversion Utilities
    # ========================================================================

    @staticmethod
    def actions_to_json(actions: Dict[str, HandAction]) -> Dict[str, Any]:
        """
        Convert HandAction dictionary to JSON-serializable format.

        Args:
            actions: Dictionary mapping hand strings to HandAction objects

        Returns:
            JSON-serializable dictionary
        """
        return {
            hand: {
                "action": action.action.value,
                "frequency": action.frequency,
                "ev": action.ev,
                "notes": action.notes
            }
            for hand, action in actions.items()
        }

    @staticmethod
    def json_to_actions(data: Dict[str, Any]) -> Dict[str, HandAction]:
        """
        Convert JSON data to HandAction dictionary.

        Args:
            data: JSON data from database or file

        Returns:
            Dictionary mapping hand strings to HandAction objects
        """
        actions = {}
        for hand, action_data in data.items():
            action = ChartAction(action_data["action"])
            actions[hand] = HandAction(
                action=action,
                frequency=action_data["frequency"],
                ev=action_data.get("ev"),
                notes=action_data.get("notes", "")
            )
        return actions

    # ========================================================================
    # Database Operations
    # ========================================================================

    def save(
        self,
        name: str,
        spot: str,
        actions: Dict[str, HandAction],
        stack_depth: int = 100,
        position_hero: str = "",
        position_villain: str = ""
    ) -> int:
        """
        Save chart to database.

        Args:
            name: Chart name
            spot: Spot/situation description
            actions: Chart actions
            stack_depth: Stack depth in big blinds
            position_hero: Hero's position
            position_villain: Villain's position

        Returns:
            Chart ID

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            chart_data = self.actions_to_json(actions)

            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO charts (name, spot, stack_depth, position_hero, position_villain, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, spot, stack_depth, position_hero, position_villain, json.dumps(chart_data)))

            self.db.connection.commit()
            chart_id = cursor.lastrowid

            if chart_id is None:
                raise DatabaseError("Failed to insert chart into database", operation="save")

            self._logger.info(f"Saved chart '{name}' with ID {chart_id}")
            return chart_id

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to save chart: {e}", operation="save")

    def load_by_id(self, chart_id: int) -> Optional[Dict[str, HandAction]]:
        """
        Load chart from database by ID.

        Args:
            chart_id: Chart ID

        Returns:
            Chart actions if found, None otherwise
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT data FROM charts WHERE id = ?", (chart_id,))
            row = cursor.fetchone()

            if not row:
                return None

            chart_data = json.loads(row[0])
            return self.json_to_actions(chart_data)

        except Exception as e:
            log_error_and_continue(e, operation="load_chart_by_id")
            return None

    def load_by_name(self, name: str) -> Optional[Dict[str, HandAction]]:
        """
        Load chart from database by name.

        Args:
            name: Chart name

        Returns:
            Chart actions if found, None otherwise
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT data FROM charts WHERE name = ? ORDER BY created_at DESC LIMIT 1",
                (name,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            chart_data = json.loads(row[0])
            return self.json_to_actions(chart_data)

        except Exception as e:
            log_error_and_continue(e, operation="load_chart_by_name")
            return None

    def list_charts(self, limit: int = 50) -> List[ChartInfo]:
        """
        List all saved charts.

        Args:
            limit: Maximum number of charts to return

        Returns:
            List of ChartInfo objects
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT id, name, spot, stack_depth, position_hero, position_villain, created_at
                FROM charts ORDER BY created_at DESC LIMIT ?
            """, (limit,))

            charts = []
            for row in cursor.fetchall():
                charts.append(ChartInfo(
                    id=row['id'],
                    name=row['name'],
                    spot=row['spot'],
                    stack_depth=row['stack_depth'],
                    position_hero=row['position_hero'],
                    position_villain=row['position_villain'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
                ))

            return charts

        except Exception as e:
            log_error_and_continue(e, operation="list_charts")
            return []

    def list_charts_as_dicts(self) -> List[Dict[str, Any]]:
        """
        List all saved charts as dictionaries.

        This method provides backward compatibility with existing code
        that expects dictionary results.

        Returns:
            List of chart dictionaries
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT id, name, spot, stack_depth, position_hero, position_villain, created_at
                FROM charts ORDER BY created_at DESC
            """)

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            log_error_and_continue(e, operation="list_charts_as_dicts")
            return []

    def delete(self, chart_id: int) -> bool:
        """
        Delete a chart from the database.

        Args:
            chart_id: Chart ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
            self.db.connection.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                self._logger.info(f"Deleted chart with ID {chart_id}")

            return deleted

        except Exception as e:
            log_error_and_continue(e, operation="delete_chart")
            return False

    def get_chart_info(self, chart_id: int) -> Optional[ChartInfo]:
        """
        Get chart metadata without loading actions.

        Args:
            chart_id: Chart ID

        Returns:
            ChartInfo if found, None otherwise
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT id, name, spot, stack_depth, position_hero, position_villain, created_at
                FROM charts WHERE id = ?
            """, (chart_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return ChartInfo(
                id=row['id'],
                name=row['name'],
                spot=row['spot'],
                stack_depth=row['stack_depth'],
                position_hero=row['position_hero'],
                position_villain=row['position_villain'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
            )

        except Exception as e:
            log_error_and_continue(e, operation="get_chart_info")
            return None


# Global repository instance
_chart_repository: Optional[ChartRepository] = None


def get_chart_repository(db: Optional[Database] = None) -> ChartRepository:
    """
    Get the global chart repository instance.

    Args:
        db: Database connection (required on first call)

    Returns:
        ChartRepository instance
    """
    global _chart_repository

    if _chart_repository is None:
        if db is None:
            from holdem_cli.storage import init_database
            db = init_database()
        _chart_repository = ChartRepository(db)

    return _chart_repository


def reset_chart_repository() -> None:
    """Reset the global chart repository (for testing)."""
    global _chart_repository
    _chart_repository = None
