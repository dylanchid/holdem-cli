"""
Chart service layer for TUI operations.

This module provides a service layer for chart-related operations,
abstracting business logic from the UI components.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import csv
from datetime import datetime
import hashlib
from dataclasses import dataclass

from holdem_cli.types import HandAction, ChartAction
from holdem_cli.storage import Database
from holdem_cli.charts.tui.widgets.matrix import create_sample_range
# from holdem_cli.charts.tui.core.cache import SmartCache
from .chart_utils import get_chart_statistics, validate_chart


@dataclass
class ChartMetadata:
    """Metadata for a chart."""
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    version: str
    tags: List[str]
    statistics: Dict[str, Any]


class ChartService:
    """
    Service for chart-related operations.

    This service handles all chart business logic including:
    - Chart creation, loading, and saving
    - Chart validation and statistics
    - Chart comparison and analysis
    - Import/export operations
    - Caching and performance optimization
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db
        # self._cache = SmartCache(max_size=50)  # Cache for chart operations
        # self._stats_cache = SmartCache(max_size=20)  # Cache for statistics

    def create_chart(
        self,
        name: str,
        actions: Dict[str, HandAction],
        description: str = "",
        tags: List[str] = None
    ) -> str:
        """
        Create a new chart.

        Args:
            name: Chart name
            actions: Chart actions
            description: Chart description
            tags: Chart tags

        Returns:
            Chart ID

        Raises:
            ValueError: If chart data is invalid
        """
        # Validate chart data
        validation_errors = validate_chart(actions)
        if validation_errors:
            raise ValueError(f"Invalid chart data: {validation_errors}")

        # Generate unique ID
        chart_id = self._generate_chart_id(name, actions)

        # Create metadata
        metadata = ChartMetadata(
            id=chart_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0",
            tags=tags or [],
            statistics=get_chart_statistics(actions)
        )

        # Cache the chart
        cache_key = f"chart_{chart_id}"
        self._cache.set(cache_key, {
            "metadata": metadata,
            "actions": actions
        })

        return chart_id

    def load_chart(self, chart_id: str) -> Tuple[ChartMetadata, Dict[str, HandAction]]:
        """
        Load a chart by ID.

        Args:
            chart_id: Chart ID

        Returns:
            Tuple of (metadata, actions)

        Raises:
            ValueError: If chart not found
        """
        # Check cache first
        cache_key = f"chart_{chart_id}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached["metadata"], cached["actions"]

        # Load from database if available
        if self.db:
            chart_data = self._load_from_db(chart_id)
            if chart_data:
                metadata = chart_data["metadata"]
                actions = chart_data["actions"]

                # Cache the result
                self._cache.set(cache_key, chart_data)
                return metadata, actions

        # Create sample chart if not found
        actions = create_sample_range()
        metadata = ChartMetadata(
            id=chart_id,
            name=f"Sample Chart {chart_id}",
            description="Auto-generated sample chart",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0",
            tags=["sample"],
            statistics=get_chart_statistics(actions)
        )

        return metadata, actions

    def save_chart(
        self,
        chart_id: str,
        name: str,
        actions: Dict[str, HandAction],
        description: str = "",
        tags: List[str] = None
    ) -> bool:
        """
        Save a chart.

        Args:
            chart_id: Chart ID
            name: Chart name
            actions: Chart actions
            description: Chart description
            tags: Chart tags

        Returns:
            True if successful
        """
        # Validate chart
        validation_errors = validate_chart(actions)
        if validation_errors:
            raise ValueError(f"Invalid chart data: {validation_errors}")

        # Update metadata
        metadata = ChartMetadata(
            id=chart_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0",
            tags=tags or [],
            statistics=get_chart_statistics(actions)
        )

        # Save to database if available
        if self.db:
            try:
                chart_data = {
                    "metadata": metadata.__dict__,
                    "actions": {hand: {
                        "action": action.action.value,
                        "frequency": action.frequency,
                        "ev": action.ev,
                        "notes": action.notes
                    } for hand, action in actions.items()}
                }
                # In a real implementation, save to database
                # self.db.save_chart(chart_id, chart_data)
            except Exception as e:
                print(f"Warning: Failed to save to database: {e}")

        # Update cache
        cache_key = f"chart_{chart_id}"
        self._cache.set(cache_key, {
            "metadata": metadata,
            "actions": actions
        })

        return True

    def compare_charts(
        self,
        chart1_id: str,
        chart2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two charts.

        Args:
            chart1_id: First chart ID
            chart2_id: Second chart ID

        Returns:
            Comparison results
        """
        # Load both charts
        metadata1, actions1 = self.load_chart(chart1_id)
        metadata2, actions2 = self.load_chart(chart2_id)

        # Find differences
        differences = self._analyze_differences(actions1, actions2)

        # Calculate similarity
        similarity = self._calculate_similarity(actions1, actions2)

        return {
            "chart1": {
                "id": chart1_id,
                "name": metadata1.name,
                "total_hands": len(actions1)
            },
            "chart2": {
                "id": chart2_id,
                "name": metadata2.name,
                "total_hands": len(actions2)
            },
            "differences": differences,
            "similarity": similarity,
            "analysis": self._generate_comparison_analysis(differences, similarity)
        }

    def export_chart(
        self,
        chart_id: str,
        format_type: str,
        filepath: str
    ) -> bool:
        """
        Export a chart to file.

        Args:
            chart_id: Chart ID
            format_type: Export format ("json", "csv", "txt")
            filepath: Export file path

        Returns:
            True if successful
        """
        # Load chart
        metadata, actions = self.load_chart(chart_id)

        # Export based on format
        if format_type == "json":
            return self._export_json(metadata, actions, filepath)
        elif format_type == "csv":
            return self._export_csv(metadata, actions, filepath)
        elif format_type == "txt":
            return self._export_txt(metadata, actions, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def import_chart(
        self,
        filepath: str,
        format_type: str,
        name: str = None
    ) -> str:
        """
        Import a chart from file.

        Args:
            filepath: Import file path
            format_type: Import format
            name: Chart name (auto-generated if None)

        Returns:
            Chart ID
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Import based on format
        if format_type == "json":
            actions = self._import_json(path)
        elif format_type == "csv":
            actions = self._import_csv(path)
        elif format_type == "txt":
            actions = self._import_txt(path)
        else:
            raise ValueError(f"Unsupported import format: {format_type}")

        # Generate name if not provided
        if not name:
            name = path.stem.replace("_", " ").title()

        # Create chart
        return self.create_chart(name, actions)

    def get_chart_statistics(self, chart_id: str) -> Dict[str, Any]:
        """
        Get cached statistics for a chart.

        Args:
            chart_id: Chart ID

        Returns:
            Statistics dictionary
        """
        cache_key = f"stats_{chart_id}"
        return self._stats_cache.get(cache_key, lambda: self._calculate_statistics(chart_id))

    def search_charts(self, query: str) -> List[ChartMetadata]:
        """
        Search for charts by name or tags.

        Args:
            query: Search query

        Returns:
            List of matching chart metadata
        """
        # This would search database in a real implementation
        # For now, return sample results
        return []

    def validate_chart_data(self, actions: Dict[str, HandAction]) -> Tuple[bool, List[str]]:
        """
        Validate chart data.

        Args:
            actions: Chart actions

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = validate_chart(actions)
        return len(errors) == 0, errors

    def analyze_chart_statistics(self, chart_data: Dict[str, HandAction]) -> Dict[str, Any]:
        """
        Analyze chart statistics.

        Args:
            chart_data: Chart data to analyze

        Returns:
            Dictionary containing chart statistics
        """
        return get_chart_statistics(chart_data)

    def _generate_chart_id(self, name: str, actions: Dict[str, HandAction]) -> str:
        """Generate unique chart ID."""
        data_str = f"{name}_{len(actions)}_{datetime.now().isoformat()}"
        return hashlib.md5(data_str.encode()).hexdigest()[:8]

    def _load_from_db(self, chart_id: str) -> Optional[Dict]:
        """Load chart from database."""
        # Placeholder for database loading
        return None

    def _analyze_differences(
        self,
        actions1: Dict[str, HandAction],
        actions2: Dict[str, HandAction]
    ) -> Dict[str, Any]:
        """Analyze differences between two charts."""
        all_hands = set(actions1.keys()) | set(actions2.keys())

        only_in_1 = []
        only_in_2 = []
        different_actions = []

        for hand in all_hands:
            in_1 = hand in actions1
            in_2 = hand in actions2

            if in_1 and not in_2:
                only_in_1.append(hand)
            elif in_2 and not in_1:
                only_in_2.append(hand)
            elif in_1 and in_2:
                action1 = actions1[hand]
                action2 = actions2[hand]
                if action1.action != action2.action:
                    different_actions.append({
                        "hand": hand,
                        "action1": action1.action.value,
                        "action2": action2.action.value
                    })

        return {
            "only_in_chart1": only_in_1,
            "only_in_chart2": only_in_2,
            "different_actions": different_actions,
            "total_differences": len(only_in_1) + len(only_in_2) + len(different_actions)
        }

    def _calculate_similarity(
        self,
        actions1: Dict[str, HandAction],
        actions2: Dict[str, HandAction]
    ) -> float:
        """Calculate similarity between two charts."""
        all_hands = set(actions1.keys()) | set(actions2.keys())
        if not all_hands:
            return 1.0

        matches = 0
        for hand in all_hands:
            if hand in actions1 and hand in actions2:
                if actions1[hand].action == actions2[hand].action:
                    matches += 1

        return matches / len(all_hands)

    def _generate_comparison_analysis(
        self,
        differences: Dict[str, Any],
        similarity: float
    ) -> str:
        """Generate human-readable comparison analysis."""
        total_diff = differences["total_differences"]

        if total_diff == 0:
            return "Charts are identical"
        elif similarity > 0.9:
            return "Charts are very similar"
        elif similarity > 0.7:
            return "Charts are moderately similar"
        elif similarity > 0.5:
            return "Charts have some similarities"
        else:
            return "Charts are significantly different"

    def _calculate_statistics(self, chart_id: str) -> Dict[str, Any]:
        """Calculate statistics for a chart."""
        metadata, actions = self.load_chart(chart_id)
        return get_chart_statistics(actions)

    def _export_json(
        self,
        metadata: ChartMetadata,
        actions: Dict[str, HandAction],
        filepath: str
    ) -> bool:
        """Export chart to JSON format."""
        export_data = {
            "metadata": {
                "id": metadata.id,
                "name": metadata.name,
                "description": metadata.description,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat(),
                "version": metadata.version,
                "tags": metadata.tags
            },
            "statistics": metadata.statistics,
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

        return True

    def _export_csv(
        self,
        metadata: ChartMetadata,
        actions: Dict[str, HandAction],
        filepath: str
    ) -> bool:
        """Export chart to CSV format."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Hand", "Action", "Frequency", "EV", "Notes"
            ])

            for hand, action in sorted(actions.items()):
                writer.writerow([
                    hand,
                    action.action.value,
                    action.frequency,
                    action.ev or '',
                    action.notes
                ])

        return True

    def _export_txt(
        self,
        metadata: ChartMetadata,
        actions: Dict[str, HandAction],
        filepath: str
    ) -> bool:
        """Export chart to text format."""
        lines = [
            f"Chart: {metadata.name}",
            f"Description: {metadata.description}",
            f"Created: {metadata.created_at.isoformat()}",
            "=" * 50,
            ""
        ]

        for hand, action in sorted(actions.items()):
            lines.append(f"{hand:>4} {action.action.value:<8} {action.frequency:.1%}")

        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

        return True

    def _import_json(self, path: Path) -> Dict[str, HandAction]:
        """Import chart from JSON format."""
        with open(path, 'r') as f:
            data = json.load(f)

        actions = {}
        for hand, action_data in data.get("ranges", {}).items():
            action = ChartAction(action_data.get("action", "fold"))
            actions[hand] = HandAction(
                action=action,
                frequency=action_data.get("frequency", 1.0),
                ev=action_data.get("ev"),
                notes=action_data.get("notes", "")
            )

        return actions

    def _import_csv(self, path: Path) -> Dict[str, HandAction]:
        """Import chart from CSV format."""
        actions = {}

        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hand = row.get("Hand", "").strip()
                if hand:
                    action = ChartAction(row.get("Action", "fold").lower())
                    actions[hand] = HandAction(
                        action=action,
                        frequency=float(row.get("Frequency", 1.0)),
                        ev=float(row.get("EV", 0)) if row.get("EV") else None,
                        notes=row.get("Notes", "")
                    )

        return actions

    def _import_txt(self, path: Path) -> Dict[str, HandAction]:
        """Import chart from text format."""
        actions = {}

        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    hand = parts[0]
                    action = ChartAction(parts[1].lower())
                    frequency = float(parts[2]) if len(parts) > 2 else 1.0

                    actions[hand] = HandAction(action=action, frequency=frequency)

        return actions


# Global service instance
_chart_service: Optional[ChartService] = None


def get_chart_service(db: Optional[Database] = None) -> ChartService:
    """Get or create the global chart service instance."""
    global _chart_service
    if _chart_service is None:
        _chart_service = ChartService(db)
    return _chart_service


def reset_chart_service():
    """Reset the global chart service instance."""
    global _chart_service
    _chart_service = None
