"""
Service container for dependency injection.

This module provides a centralized container for managing service instances,
replacing scattered global singletons with a more testable and maintainable pattern.

Usage:
    from holdem_cli.services.container import get_container, ServiceContainer

    # Get services from container
    container = get_container()
    chart_service = container.chart_service
    db_service = container.db_service

    # For testing, create isolated container
    test_container = ServiceContainer()
    test_container.initialize()
"""

from typing import Optional, TYPE_CHECKING
from holdem_cli.utils.logging_utils import get_logger

if TYPE_CHECKING:
    from holdem_cli.storage import Database
    from holdem_cli.services.charts.chart_repository import ChartRepository
    from holdem_cli.services.charts.chart_service import ChartService
    from holdem_cli.services.charts.navigation_service import NavigationService
    from holdem_cli.services.charts.ui_service import UIService
    from holdem_cli.services.charts.db_service import DatabaseService
    from holdem_cli.services.charts.quiz_service import QuizService
    from holdem_cli.charts.tui.core.events import EventBus
    from holdem_cli.charts.tui.core.error_handler import ErrorHandler


class ServiceContainer:
    """
    Central container for managing service instances.

    This container provides lazy initialization of services with proper
    dependency management and cleanup support.
    """

    def __init__(self) -> None:
        """Initialize empty container."""
        self._logger = get_logger()
        self._initialized = False

        # Core infrastructure
        self._database: Optional["Database"] = None
        self._event_bus: Optional["EventBus"] = None
        self._error_handler: Optional["ErrorHandler"] = None

        # Chart services
        self._chart_repository: Optional["ChartRepository"] = None
        self._chart_service: Optional["ChartService"] = None
        self._navigation_service: Optional["NavigationService"] = None
        self._ui_service: Optional["UIService"] = None
        self._db_service: Optional["DatabaseService"] = None
        self._quiz_service: Optional["QuizService"] = None

    def initialize(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the container with all services.

        Args:
            db_path: Optional custom database path
        """
        if self._initialized:
            return

        self._logger.info("Initializing service container")

        # Initialize database first (other services depend on it)
        from holdem_cli.storage import init_database
        self._database = init_database(db_path)

        self._initialized = True
        self._logger.info("Service container initialized")

    @property
    def database(self) -> "Database":
        """Get database connection."""
        if self._database is None:
            self.initialize()
        return self._database  # type: ignore

    @property
    def event_bus(self) -> "EventBus":
        """Get event bus instance."""
        if self._event_bus is None:
            from holdem_cli.charts.tui.core.events import EventBus
            self._event_bus = EventBus()
        return self._event_bus

    @property
    def error_handler(self) -> "ErrorHandler":
        """Get error handler instance."""
        if self._error_handler is None:
            from holdem_cli.charts.tui.core.error_handler import ErrorHandler
            self._error_handler = ErrorHandler()
        return self._error_handler

    @property
    def chart_repository(self) -> "ChartRepository":
        """Get chart repository instance."""
        if self._chart_repository is None:
            from holdem_cli.services.charts.chart_repository import ChartRepository
            self._chart_repository = ChartRepository(self.database)
        return self._chart_repository

    @property
    def chart_service(self) -> "ChartService":
        """Get chart service instance."""
        if self._chart_service is None:
            from holdem_cli.services.charts.chart_service import ChartService
            self._chart_service = ChartService()
        return self._chart_service

    @property
    def navigation_service(self) -> "NavigationService":
        """Get navigation service instance."""
        if self._navigation_service is None:
            from holdem_cli.services.charts.navigation_service import NavigationService
            self._navigation_service = NavigationService()
        return self._navigation_service

    @property
    def ui_service(self) -> "UIService":
        """Get UI service instance."""
        if self._ui_service is None:
            from holdem_cli.services.charts.ui_service import UIService
            self._ui_service = UIService()
        return self._ui_service

    @property
    def db_service(self) -> "DatabaseService":
        """Get database service instance."""
        if self._db_service is None:
            from holdem_cli.services.charts.db_service import DatabaseService
            self._db_service = DatabaseService()
        return self._db_service

    @property
    def quiz_service(self) -> "QuizService":
        """Get quiz service instance."""
        if self._quiz_service is None:
            from holdem_cli.services.charts.quiz_service import QuizService
            self._quiz_service = QuizService()
        return self._quiz_service

    def cleanup(self) -> None:
        """
        Clean up all services and release resources.

        Call this when shutting down the application.
        """
        self._logger.info("Cleaning up service container")

        # Close database connection
        if self._database is not None:
            try:
                self._database.close()
            except Exception as e:
                self._logger.warning(f"Error closing database: {e}")
            self._database = None

        # Reset all service instances
        self._event_bus = None
        self._error_handler = None
        self._chart_repository = None
        self._chart_service = None
        self._navigation_service = None
        self._ui_service = None
        self._db_service = None
        self._quiz_service = None

        self._initialized = False
        self._logger.info("Service container cleaned up")

    def reset(self) -> None:
        """
        Reset container for testing.

        This cleans up existing services and allows re-initialization.
        """
        self.cleanup()

    def __enter__(self) -> "ServiceContainer":
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """
    Get the global service container instance.

    Returns:
        ServiceContainer: The global container
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_container() -> None:
    """
    Reset the global container.

    Use this for testing to ensure clean state between tests.
    """
    global _container
    if _container is not None:
        _container.cleanup()
    _container = None


def initialize_container(db_path: Optional[str] = None) -> ServiceContainer:
    """
    Initialize and return the global container.

    Args:
        db_path: Optional custom database path

    Returns:
        ServiceContainer: The initialized global container
    """
    container = get_container()
    container.initialize(db_path)
    return container
