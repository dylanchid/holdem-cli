"""Tests for the ServiceContainer class."""

import pytest
from unittest.mock import patch, MagicMock

from holdem_cli.services.container import (
    ServiceContainer,
    get_container,
    reset_container,
    initialize_container
)


class TestServiceContainer:
    """Tests for ServiceContainer initialization and cleanup."""

    def setup_method(self):
        """Reset container before each test."""
        reset_container()

    def teardown_method(self):
        """Clean up after each test."""
        reset_container()

    def test_container_creation(self):
        """Test that container can be created."""
        container = ServiceContainer()
        assert container is not None
        assert not container._initialized

    def test_lazy_initialization(self):
        """Test that services are lazily initialized."""
        container = ServiceContainer()

        # Container starts uninitialized
        assert container._database is None
        assert container._chart_service is None
        assert container._navigation_service is None

    def test_database_initialization(self):
        """Test that database is initialized on first access."""
        container = ServiceContainer()

        # Access database triggers initialization
        db = container.database
        assert db is not None
        assert container._initialized

        # Clean up
        container.cleanup()

    def test_chart_service_initialization(self):
        """Test that chart service is initialized on first access."""
        container = ServiceContainer()
        container.initialize()

        service = container.chart_service
        assert service is not None
        assert container._chart_service is not None

        container.cleanup()

    def test_navigation_service_initialization(self):
        """Test that navigation service is initialized on first access."""
        container = ServiceContainer()
        container.initialize()

        service = container.navigation_service
        assert service is not None
        assert container._navigation_service is not None

        container.cleanup()

    def test_ui_service_initialization(self):
        """Test that UI service is initialized on first access."""
        container = ServiceContainer()
        container.initialize()

        service = container.ui_service
        assert service is not None
        assert container._ui_service is not None

        container.cleanup()

    def test_cleanup(self):
        """Test that cleanup resets all services."""
        container = ServiceContainer()
        container.initialize()

        # Access services to initialize them
        _ = container.chart_service
        _ = container.navigation_service
        _ = container.ui_service

        # Cleanup should reset everything
        container.cleanup()

        assert container._database is None
        assert container._chart_service is None
        assert container._navigation_service is None
        assert container._ui_service is None
        assert not container._initialized

    def test_reset(self):
        """Test that reset is an alias for cleanup."""
        container = ServiceContainer()
        container.initialize()

        _ = container.chart_service

        container.reset()

        assert container._chart_service is None
        assert not container._initialized

    def test_context_manager(self):
        """Test that container works as context manager."""
        with ServiceContainer() as container:
            assert container._initialized
            _ = container.chart_service
            assert container._chart_service is not None

        # After context exit, should be cleaned up
        assert container._chart_service is None

    def test_multiple_access_returns_same_instance(self):
        """Test that multiple accesses return the same service instance."""
        container = ServiceContainer()
        container.initialize()

        service1 = container.chart_service
        service2 = container.chart_service

        assert service1 is service2

        container.cleanup()


class TestGlobalContainer:
    """Tests for global container functions."""

    def setup_method(self):
        """Reset container before each test."""
        reset_container()

    def teardown_method(self):
        """Clean up after each test."""
        reset_container()

    def test_get_container_creates_singleton(self):
        """Test that get_container returns the same instance."""
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_reset_container(self):
        """Test that reset_container clears the global instance."""
        container1 = get_container()
        container1.initialize()

        reset_container()

        container2 = get_container()

        # Should be a new instance
        assert container2 is not container1
        assert not container2._initialized

    def test_initialize_container(self):
        """Test that initialize_container initializes and returns container."""
        container = initialize_container()

        assert container is not None
        assert container._initialized
        assert container is get_container()


class TestServiceContainerIntegration:
    """Integration tests for ServiceContainer with actual services."""

    def setup_method(self):
        """Reset container before each test."""
        reset_container()

    def teardown_method(self):
        """Clean up after each test."""
        reset_container()

    def test_all_services_accessible(self):
        """Test that all services can be accessed."""
        container = ServiceContainer()
        container.initialize()

        # All these should work without error
        assert container.database is not None
        assert container.chart_service is not None
        assert container.navigation_service is not None
        assert container.ui_service is not None
        assert container.db_service is not None
        assert container.quiz_service is not None
        assert container.event_bus is not None
        assert container.error_handler is not None
        assert container.chart_repository is not None

        container.cleanup()

    def test_services_share_database(self):
        """Test that services initialized from same container share database."""
        container = ServiceContainer()
        container.initialize()

        db = container.database
        repo = container.chart_repository

        # Repository should use the same database
        assert repo.db is db

        container.cleanup()
