"""
Tests for database service layer.

This module tests the DatabaseService class and related functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
setup_test_imports()

from holdem_cli.services.charts.db_service import (
    DatabaseService, DatabaseConfig, DatabaseError,
    get_database_service, reset_database_service
)
from holdem_cli.services.charts.chart_service import ChartMetadata
from holdem_cli.charts.tui.widgets.matrix import HandAction, ChartAction


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def db_config():
    """Create an in-memory database config for testing."""
    return DatabaseConfig(path=":memory:")


@pytest.fixture
def db_service(db_config):
    """Create a database service for testing."""
    service = DatabaseService(db_config)
    yield service
    service.close()


@pytest.fixture
def sample_metadata():
    """Create sample chart metadata for testing."""
    return ChartMetadata(
        id="test-chart-123",
        name="Test Chart",
        description="A test chart for unit testing",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version="1.0",
        tags=["test", "sample"],
        statistics={"total_hands": 10, "actions": {"raise": 5, "fold": 5}}
    )


@pytest.fixture
def sample_actions():
    """Create sample chart actions for testing."""
    return {
        "AA": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=2.5, notes="Premium"),
        "KK": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=2.0, notes="Premium"),
        "QQ": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=1.5, notes="Strong"),
        "AKs": HandAction(action=ChartAction.RAISE, frequency=0.9, ev=1.0, notes="Suited"),
        "AKo": HandAction(action=ChartAction.RAISE, frequency=0.8, ev=0.8, notes="Offsuit"),
        "72o": HandAction(action=ChartAction.FOLD, frequency=1.0, ev=-0.5, notes="Trash"),
    }


# =============================================================================
# DatabaseConfig Tests
# =============================================================================

class TestDatabaseConfig:
    def test_default_values(self):
        config = DatabaseConfig()
        assert config.path == ":memory:"
        assert config.timeout == 5.0
        assert config.enable_foreign_keys is True
        assert config.enable_wal_mode is True

    def test_custom_values(self):
        config = DatabaseConfig(
            path="/tmp/test.db",
            timeout=10.0,
            enable_foreign_keys=False,
            enable_wal_mode=False
        )
        assert config.path == "/tmp/test.db"
        assert config.timeout == 10.0
        assert config.enable_foreign_keys is False
        assert config.enable_wal_mode is False


# =============================================================================
# DatabaseError Tests
# =============================================================================

class TestDatabaseError:
    def test_error_message(self):
        error = DatabaseError("Test error message")
        assert str(error) == "Test error message"

    def test_error_is_exception(self):
        assert issubclass(DatabaseError, Exception)


# =============================================================================
# DatabaseService Connection Tests
# =============================================================================

class TestDatabaseServiceConnection:
    def test_initialization(self, db_config):
        service = DatabaseService(db_config)
        assert service.config == db_config
        service.close()

    def test_default_config(self):
        service = DatabaseService()
        assert service.config.path == ":memory:"
        service.close()

    def test_close(self, db_service):
        # Should not raise
        db_service.close()
        # Should be safe to call multiple times
        db_service.close()


# =============================================================================
# DatabaseService Chart Operations Tests
# =============================================================================

class TestDatabaseServiceCharts:
    def test_save_and_load_chart(self, db_service, sample_metadata, sample_actions):
        # Save chart
        result = db_service.save_chart(
            sample_metadata.id,
            sample_metadata,
            sample_actions
        )
        assert result is True

        # Load chart
        loaded_metadata, loaded_actions = db_service.load_chart(sample_metadata.id)

        assert loaded_metadata is not None
        assert loaded_actions is not None
        assert loaded_metadata.id == sample_metadata.id
        assert loaded_metadata.name == sample_metadata.name
        assert len(loaded_actions) == len(sample_actions)

    def test_load_nonexistent_chart(self, db_service):
        metadata, actions = db_service.load_chart("nonexistent-id")
        assert metadata is None
        assert actions is None

    def test_save_chart_updates_existing(self, db_service, sample_metadata, sample_actions):
        # Save original
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)

        # Update metadata
        updated_metadata = ChartMetadata(
            id=sample_metadata.id,
            name="Updated Chart",
            description="Updated description",
            created_at=sample_metadata.created_at,
            updated_at=datetime.now(),
            version="2.0",
            tags=["updated"],
            statistics=sample_metadata.statistics
        )

        # Save updated
        db_service.save_chart(sample_metadata.id, updated_metadata, sample_actions)

        # Load and verify
        loaded_metadata, loaded_actions = db_service.load_chart(sample_metadata.id)
        assert loaded_metadata.name == "Updated Chart"
        assert loaded_metadata.version == "2.0"

    def test_list_charts_empty(self, db_service):
        charts = db_service.list_charts()
        assert charts == []

    def test_list_charts(self, db_service, sample_metadata, sample_actions):
        # Save multiple charts
        for i in range(3):
            meta = ChartMetadata(
                id=f"chart-{i}",
                name=f"Chart {i}",
                description="Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0",
                tags=[],
                statistics={}
            )
            db_service.save_chart(meta.id, meta, sample_actions)

        # List charts
        charts = db_service.list_charts()
        assert len(charts) == 3

    def test_list_charts_with_limit(self, db_service, sample_actions):
        # Save 5 charts
        for i in range(5):
            meta = ChartMetadata(
                id=f"chart-{i}",
                name=f"Chart {i}",
                description="Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0",
                tags=[],
                statistics={}
            )
            db_service.save_chart(meta.id, meta, sample_actions)

        # List with limit
        charts = db_service.list_charts(limit=3)
        assert len(charts) == 3

    def test_list_charts_with_offset(self, db_service, sample_actions):
        # Save 5 charts
        for i in range(5):
            meta = ChartMetadata(
                id=f"chart-{i}",
                name=f"Chart {i}",
                description="Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0",
                tags=[],
                statistics={}
            )
            db_service.save_chart(meta.id, meta, sample_actions)

        # List with offset
        charts = db_service.list_charts(limit=10, offset=3)
        assert len(charts) == 2

    def test_delete_chart(self, db_service, sample_metadata, sample_actions):
        # Save chart
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)

        # Delete chart
        result = db_service.delete_chart(sample_metadata.id)
        assert result is True

        # Verify deleted
        metadata, actions = db_service.load_chart(sample_metadata.id)
        assert metadata is None

    def test_delete_nonexistent_chart(self, db_service):
        result = db_service.delete_chart("nonexistent-id")
        assert result is False

    def test_search_charts(self, db_service, sample_actions):
        # Save charts with different names
        for name in ["BTN vs BB", "CO vs BTN", "UTG Open"]:
            meta = ChartMetadata(
                id=name.lower().replace(" ", "-"),
                name=name,
                description="Test chart",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0",
                tags=[],
                statistics={}
            )
            db_service.save_chart(meta.id, meta, sample_actions)

        # Search for BTN
        results = db_service.search_charts("BTN")
        assert len(results) == 2

        # Search for Open
        results = db_service.search_charts("Open")
        assert len(results) == 1
        assert results[0].name == "UTG Open"

    def test_search_charts_no_results(self, db_service):
        results = db_service.search_charts("nonexistent")
        assert results == []


# =============================================================================
# DatabaseService Session Tests
# =============================================================================

class TestDatabaseServiceSessions:
    def test_save_session(self, db_service):
        result = db_service.save_session(
            session_id="session-123",
            session_type="quiz",
            chart_id=None,
            score=85.5,
            metadata={"questions": 10, "correct": 8}
        )
        assert result is True

    def test_save_session_minimal(self, db_service):
        result = db_service.save_session(
            session_id="session-456",
            session_type="game",
            chart_id=None
        )
        assert result is True


# =============================================================================
# DatabaseService Preferences Tests
# =============================================================================

class TestDatabaseServicePreferences:
    def test_set_and_get_preference(self, db_service):
        # Set preference
        result = db_service.set_preference("theme", "dark")
        assert result is True

        # Get preference
        value = db_service.get_preference("theme")
        assert value == "dark"

    def test_get_nonexistent_preference(self, db_service):
        value = db_service.get_preference("nonexistent")
        assert value is None

    def test_get_preference_with_default(self, db_service):
        value = db_service.get_preference("nonexistent", default="default_value")
        assert value == "default_value"

    def test_set_preference_complex_value(self, db_service):
        # Set complex preference
        complex_value = {
            "colors": ["red", "green", "blue"],
            "settings": {"enabled": True, "count": 5}
        }
        db_service.set_preference("display_config", complex_value)

        # Get and verify
        value = db_service.get_preference("display_config")
        assert value == complex_value

    def test_update_preference(self, db_service):
        # Set initial
        db_service.set_preference("count", 1)

        # Update
        db_service.set_preference("count", 2)

        # Verify
        value = db_service.get_preference("count")
        assert value == 2


# =============================================================================
# DatabaseService Stats and Optimization Tests
# =============================================================================

class TestDatabaseServiceStats:
    def test_get_database_stats_empty(self, db_service):
        stats = db_service.get_database_stats()
        assert stats['total_charts'] == 0
        assert stats['total_actions'] == 0
        assert stats['total_sessions'] == 0

    def test_get_database_stats(self, db_service, sample_metadata, sample_actions):
        # Add some data
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)
        db_service.save_session("session-1", "quiz", None)

        # Get stats
        stats = db_service.get_database_stats()
        assert stats['total_charts'] == 1
        assert stats['total_actions'] == 6
        assert stats['total_sessions'] == 1

    def test_optimize_database(self, db_service, sample_metadata, sample_actions):
        # Add data first
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)

        # Optimize should succeed
        result = db_service.optimize_database()
        assert result is True


# =============================================================================
# DatabaseService Backup Tests
# =============================================================================

class TestDatabaseServiceBackup:
    def test_backup_database(self, db_service, sample_metadata, sample_actions):
        # Add some data
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)

        # Create backup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            backup_path = f.name

        try:
            result = db_service.backup_database(backup_path)
            assert result is True
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
        finally:
            os.unlink(backup_path)


# =============================================================================
# DatabaseService Caching Tests
# =============================================================================

class TestDatabaseServiceCaching:
    def test_load_chart_caches_result(self, db_service, sample_metadata, sample_actions):
        # Save chart
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)

        # Load twice
        metadata1, actions1 = db_service.load_chart(sample_metadata.id)
        metadata2, actions2 = db_service.load_chart(sample_metadata.id)

        # Should return same cached objects
        assert metadata1 is metadata2
        assert actions1 is actions2

    def test_save_chart_clears_cache(self, db_service, sample_metadata, sample_actions):
        # Save initial
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)

        # Load to cache
        db_service.load_chart(sample_metadata.id)

        # Update and save again
        updated_actions = {"AA": HandAction(action=ChartAction.FOLD, frequency=1.0)}
        db_service.save_chart(sample_metadata.id, sample_metadata, updated_actions)

        # Load should get new data
        _, loaded_actions = db_service.load_chart(sample_metadata.id)
        assert len(loaded_actions) == 1

    def test_delete_chart_clears_cache(self, db_service, sample_metadata, sample_actions):
        # Save and load to cache
        db_service.save_chart(sample_metadata.id, sample_metadata, sample_actions)
        db_service.load_chart(sample_metadata.id)

        # Delete
        db_service.delete_chart(sample_metadata.id)

        # Cache should be cleared
        metadata, actions = db_service.load_chart(sample_metadata.id)
        assert metadata is None


# =============================================================================
# Global Service Tests
# =============================================================================

class TestGlobalDatabaseService:
    def test_get_database_service(self):
        # Reset first
        reset_database_service()

        # Get service
        service = get_database_service()
        assert service is not None
        assert isinstance(service, DatabaseService)

        # Get again returns same instance
        service2 = get_database_service()
        assert service is service2

        # Cleanup
        reset_database_service()

    def test_reset_database_service(self):
        # Get service
        service = get_database_service()

        # Reset
        reset_database_service()

        # Get new service
        service2 = get_database_service()
        assert service is not service2

        # Cleanup
        reset_database_service()


# =============================================================================
# Integration Tests
# =============================================================================

class TestDatabaseServiceIntegration:
    def test_full_workflow(self, db_service, sample_actions):
        """Test a complete workflow of database operations."""
        # 1. Create and save a chart
        metadata = ChartMetadata(
            id="workflow-test",
            name="Workflow Test Chart",
            description="Testing full workflow",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0",
            tags=["test", "workflow"],
            statistics={"total_hands": len(sample_actions)}
        )
        db_service.save_chart(metadata.id, metadata, sample_actions)

        # 2. Load and verify
        loaded_meta, loaded_actions = db_service.load_chart(metadata.id)
        assert loaded_meta.name == "Workflow Test Chart"
        assert len(loaded_actions) == len(sample_actions)

        # 3. Search for it
        results = db_service.search_charts("Workflow")
        assert len(results) == 1

        # 4. List all charts
        charts = db_service.list_charts()
        assert len(charts) == 1

        # 5. Save a session (without chart_id to avoid FK constraint on delete)
        db_service.save_session("test-session", "quiz", None, score=90.0)

        # 6. Set some preferences
        db_service.set_preference("last_chart", metadata.id)
        assert db_service.get_preference("last_chart") == metadata.id

        # 7. Check stats
        stats = db_service.get_database_stats()
        assert stats['total_charts'] == 1
        assert stats['total_sessions'] == 1

        # 8. Delete chart
        db_service.delete_chart(metadata.id)
        assert db_service.load_chart(metadata.id) == (None, None)

    def test_multiple_charts_workflow(self, db_service, sample_actions):
        """Test operations with multiple charts."""
        # Create multiple charts
        chart_ids = []
        for i in range(5):
            meta = ChartMetadata(
                id=f"multi-chart-{i}",
                name=f"Multi Chart {i}",
                description=f"Description for chart {i}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0",
                tags=[f"tag{i}"],
                statistics={}
            )
            db_service.save_chart(meta.id, meta, sample_actions)
            chart_ids.append(meta.id)

        # List all
        charts = db_service.list_charts()
        assert len(charts) == 5

        # Search
        results = db_service.search_charts("Multi")
        assert len(results) == 5

        # Delete one
        db_service.delete_chart(chart_ids[0])
        charts = db_service.list_charts()
        assert len(charts) == 4

        # Stats should reflect changes
        stats = db_service.get_database_stats()
        assert stats['total_charts'] == 4
