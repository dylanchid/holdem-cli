"""
Performance optimization system for TUI components.

This module provides performance monitoring, caching optimization,
and render performance improvements for the TUI application.
"""

from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
import time
import asyncio
import functools
from weakref import WeakSet
import gc

from ..core.cache import SmartCache
from ..core.events import get_event_bus, EventType


class PerformanceMetrics:
    """Container for performance metrics."""

    def __init__(self):
        self.render_times: List[float] = []
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.memory_usage: List[float] = []
        self.event_processing_times: List[float] = []
        self.start_time = datetime.now()

    def add_render_time(self, duration: float):
        """Add render time measurement."""
        self.render_times.append(duration)
        if len(self.render_times) > 100:
            self.render_times.pop(0)

    def add_memory_usage(self, usage: float):
        """Add memory usage measurement."""
        self.memory_usage.append(usage)
        if len(self.memory_usage) > 50:
            self.memory_usage.pop(0)

    def get_average_render_time(self) -> float:
        """Get average render time."""
        return sum(self.render_times) / len(self.render_times) if self.render_times else 0

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0

    def get_memory_trend(self) -> str:
        """Get memory usage trend."""
        if len(self.memory_usage) < 2:
            return "stable"

        recent = self.memory_usage[-5:]
        if len(recent) < 2:
            return "stable"

        avg_recent = sum(recent) / len(recent)
        avg_older = sum(self.memory_usage[:-5]) / len(self.memory_usage[:-5]) if len(self.memory_usage) > 5 else avg_recent

        if avg_recent > avg_older * 1.1:
            return "increasing"
        elif avg_recent < avg_older * 0.9:
            return "decreasing"
        else:
            return "stable"

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "average_render_time_ms": self.get_average_render_time() * 1000,
            "cache_hit_rate": self.get_cache_hit_rate(),
            "memory_trend": self.get_memory_trend(),
            "total_renders": len(self.render_times),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


class PerformanceOptimizer:
    """
    Performance optimization system.

    Features:
    - Smart caching with TTL and LRU eviction
    - Lazy loading for heavy components
    - Render optimization with dirty checking
    - Memory management and garbage collection hints
    - Performance monitoring and metrics
    """

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.render_cache = SmartCache(max_size=100, default_ttl=timedelta(minutes=5))
        self.data_cache = SmartCache(max_size=200, default_ttl=timedelta(minutes=10))
        self._event_bus = get_event_bus()
        self._dirty_components: Set[str] = set()
        self._lazy_components: Dict[str, Callable] = {}
        self._optimization_enabled = True

    def enable_optimization(self, enabled: bool = True):
        """Enable or disable performance optimizations."""
        self._optimization_enabled = enabled

    def measure_memory_usage(self) -> float:
        """Measure current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            # Fallback: use garbage collector stats
            return len(gc.get_objects()) / 1000  # Rough approximation

    def optimize_memory(self):
        """Run memory optimization."""
        # Force garbage collection
        gc.collect()

        # Clear unused caches
        self.render_cache.clear()
        self.data_cache.clear()

        # Clear dirty components
        self._dirty_components.clear()

        # Update metrics
        memory_usage = self.measure_memory_usage()
        self.metrics.add_memory_usage(memory_usage)

    def cached_render(self, component_id: str, render_func: Callable, *args, **kwargs):
        """Cache render results for components."""
        if not self._optimization_enabled:
            return render_func(*args, **kwargs)

        cache_key = f"render_{component_id}_{hash(str(args) + str(kwargs))}"

        def compute():
            start_time = time.time()
            result = render_func(*args, **kwargs)
            duration = time.time() - start_time
            self.metrics.add_render_time(duration)
            return result

        cached_result = self.render_cache.get(cache_key, compute)

        if cached_result is not None:
            self.metrics.cache_hits += 1
            return cached_result
        else:
            self.metrics.cache_misses += 1
            return compute()

    def cached_data(self, data_key: str, fetch_func: Callable, *args, **kwargs):
        """Cache data fetching operations."""
        if not self._optimization_enabled:
            return fetch_func(*args, **kwargs)

        def compute():
            return fetch_func(*args, **kwargs)

        cached_result = self.data_cache.get(data_key, compute)

        if cached_result is not None:
            self.metrics.cache_hits += 1
            return cached_result
        else:
            self.metrics.cache_misses += 1
            return compute()

    def mark_dirty(self, component_id: str):
        """Mark a component as dirty (needs re-render)."""
        self._dirty_components.add(component_id)

        # Invalidate related cache entries
        self._invalidate_component_cache(component_id)

    def is_dirty(self, component_id: str) -> bool:
        """Check if a component is dirty."""
        return component_id in self._dirty_components

    def clear_dirty(self, component_id: str):
        """Clear dirty status for a component."""
        self._dirty_components.discard(component_id)

    def register_lazy_component(self, component_id: str, load_func: Callable):
        """Register a component for lazy loading."""
        self._lazy_components[component_id] = load_func

    def load_lazy_component(self, component_id: str):
        """Load a lazy component."""
        if component_id in self._lazy_components:
            load_func = self._lazy_components[component_id]
            return load_func()
        return None

    def _invalidate_component_cache(self, component_id: str):
        """Invalidate cache entries for a component."""
        # Remove render cache entries for this component
        keys_to_remove = [key for key in self.render_cache._cache.keys()
                         if key.startswith(f"render_{component_id}")]
        for key in keys_to_remove:
            del self.render_cache._cache[key]

    def get_optimization_suggestions(self) -> List[str]:
        """Get optimization suggestions based on current metrics."""
        suggestions = []

        # Check render performance
        avg_render_time = self.metrics.get_average_render_time()
        if avg_render_time > 0.1:  # More than 100ms
            suggestions.append("Render times are high - consider reducing component complexity")
        elif avg_render_time > 0.05:  # More than 50ms
            suggestions.append("Render times are moderate - consider caching optimizations")

        # Check cache performance
        cache_hit_rate = self.metrics.get_cache_hit_rate()
        if cache_hit_rate < 0.5:
            suggestions.append("Cache hit rate is low - consider adjusting cache size or TTL")
        elif cache_hit_rate > 0.95:
            suggestions.append("Cache hit rate is very high - cache might be too large")

        # Check memory usage
        memory_trend = self.metrics.get_memory_trend()
        if memory_trend == "increasing":
            suggestions.append("Memory usage is increasing - consider running garbage collection")
        elif memory_trend == "stable" and self.measure_memory_usage() > 100:  # > 100MB
            suggestions.append("Memory usage is high but stable - consider optimization")

        return suggestions

    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        memory_usage = self.measure_memory_usage()
        self.metrics.add_memory_usage(memory_usage)

        return {
            "metrics": self.metrics.get_performance_summary(),
            "optimization_enabled": self._optimization_enabled,
            "dirty_components": len(self._dirty_components),
            "cached_renders": len(self.render_cache._cache),
            "cached_data": len(self.data_cache._cache),
            "lazy_components": len(self._lazy_components),
            "suggestions": self.get_optimization_suggestions()
        }


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create the global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def reset_performance_optimizer():
    """Reset the global performance optimizer instance."""
    global _performance_optimizer
    _performance_optimizer = None


# Decorators for performance optimization
def cached_render(component_id: str):
    """Decorator to cache render results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            return optimizer.cached_render(component_id, func, *args, **kwargs)
        return wrapper
    return decorator


def cached_data(data_key_template: str):
    """Decorator to cache data fetching operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()

            # Format data key with arguments if template contains placeholders
            try:
                data_key = data_key_template.format(*args, **kwargs)
            except (IndexError, KeyError):
                data_key = f"{data_key_template}_{hash((args, tuple(kwargs.items())))}"

            return optimizer.cached_data(data_key, func, *args, **kwargs)
        return wrapper
    return decorator


def lazy_load(component_id: str):
    """Decorator to mark a component as lazy-loaded."""
    def decorator(func: Callable) -> Callable:
        optimizer = get_performance_optimizer()
        optimizer.register_lazy_component(component_id, func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Return a placeholder that will be loaded when needed
            return f"LazyComponent({component_id})"
        return wrapper
    return decorator


def measure_performance(operation_name: str):
    """Decorator to measure operation performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                optimizer = get_performance_optimizer()
                optimizer.metrics.add_render_time(duration)
        return wrapper
    return decorator


# Utility functions for performance monitoring
def start_performance_monitoring(interval: float = 5.0):
    """Start background performance monitoring."""
    async def monitor():
        optimizer = get_performance_optimizer()
        while True:
            await asyncio.sleep(interval)

            # Update memory metrics
            memory_usage = optimizer.measure_memory_usage()
            optimizer.metrics.add_memory_usage(memory_usage)

            # Log performance issues
            suggestions = optimizer.get_optimization_suggestions()
            if suggestions:
                print(f"Performance suggestions: {suggestions}")

            # Trigger garbage collection if memory is high
            if memory_usage > 200:  # 200MB threshold
                gc.collect()

    # Start monitoring task
    asyncio.create_task(monitor())


def get_memory_usage_report() -> Dict[str, Any]:
    """Get detailed memory usage report."""
    try:
        import psutil
        process = psutil.Process()

        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "shared_mb": memory_info.shared / 1024 / 1024,
            "memory_percent": memory_percent,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024
        }
    except ImportError:
        # Fallback report
        return {
            "objects_count": len(gc.get_objects()),
            "garbage_count": len(gc.garbage),
            "note": "Install psutil for detailed memory report"
        }


def optimize_for_low_memory():
    """Apply optimizations for low memory environments."""
    optimizer = get_performance_optimizer()

    # Reduce cache sizes
    optimizer.render_cache._max_size = 50
    optimizer.data_cache._max_size = 100

    # Clear existing caches
    optimizer.render_cache.clear()
    optimizer.data_cache.clear()

    # Force garbage collection
    gc.collect()

    # Disable some optimizations if needed
    optimizer.enable_optimization(False)


class MemoryManager:
    """
    Advanced memory management system for chart data and large objects.

    Features:
    - Weak references for temporary chart data
    - Automatic cleanup of unused chart objects
    - Memory pressure monitoring
    - Smart caching with size limits
    - Memory-efficient data structures
    """

    def __init__(self, max_chart_cache_size: int = 10, max_matrix_cache_size: int = 5):
        self.chart_cache = {}
        self.matrix_cache = {}
        self.weak_refs = set()
        self.max_chart_cache_size = max_chart_cache_size
        self.max_matrix_cache_size = max_matrix_cache_size
        self._memory_threshold = 200 * 1024 * 1024  # 200MB

    def cache_chart_data(self, chart_id: str, chart_data: Dict, strong_ref: bool = False):
        """Cache chart data with optional weak referencing."""
        if strong_ref:
            # Strong reference for frequently used charts
            if len(self.chart_cache) >= self.max_chart_cache_size:
                # Remove oldest entry (simple LRU)
                oldest_key = next(iter(self.chart_cache))
                del self.chart_cache[oldest_key]
            self.chart_cache[chart_id] = chart_data
        else:
            # Weak reference for temporary data
            import weakref
            weak_ref = weakref.ref(chart_data, lambda ref: self._cleanup_weak_ref(ref, chart_id))
            self.weak_refs.add((chart_id, weak_ref))

    def get_chart_data(self, chart_id: str):
        """Get chart data from cache."""
        # Check strong cache first
        if chart_id in self.chart_cache:
            return self.chart_cache[chart_id]

        # Check weak references
        for ref_id, weak_ref in self.weak_refs.copy():
            if ref_id == chart_id:
                data = weak_ref()
                if data is not None:
                    return data
                else:
                    # Reference is dead, clean it up
                    self.weak_refs.discard((ref_id, weak_ref))

        return None

    def cache_matrix(self, matrix_id: str, matrix_data, strong_ref: bool = False):
        """Cache matrix data with memory management."""
        if strong_ref:
            if len(self.matrix_cache) >= self.max_matrix_cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.matrix_cache))
                del self.matrix_cache[oldest_key]
            self.matrix_cache[matrix_id] = matrix_data
        else:
            # Use weak reference for temporary matrices
            import weakref
            weak_ref = weakref.ref(matrix_data, lambda ref: self._cleanup_matrix_ref(ref, matrix_id))
            self.weak_refs.add((f"matrix_{matrix_id}", weak_ref))

    def get_matrix(self, matrix_id: str):
        """Get matrix data from cache."""
        # Check strong cache first
        if matrix_id in self.matrix_cache:
            return self.matrix_cache[matrix_id]

        # Check weak references
        for ref_id, weak_ref in self.weak_refs.copy():
            if ref_id == f"matrix_{matrix_id}":
                data = weak_ref()
                if data is not None:
                    return data
                else:
                    # Reference is dead, clean it up
                    self.weak_refs.discard((ref_id, weak_ref))

        return None

    def _cleanup_weak_ref(self, weak_ref, chart_id: str):
        """Cleanup callback for weak references."""
        self.weak_refs.discard((chart_id, weak_ref))

    def _cleanup_matrix_ref(self, weak_ref, matrix_id: str):
        """Cleanup callback for matrix weak references."""
        self.weak_refs.discard((f"matrix_{matrix_id}", weak_ref))

    def clear_caches(self):
        """Clear all caches."""
        self.chart_cache.clear()
        self.matrix_cache.clear()
        self.weak_refs.clear()
        gc.collect()

    def optimize_memory_usage(self):
        """Optimize memory usage by cleaning up unused objects."""
        # Remove dead weak references
        dead_refs = []
        for ref_id, weak_ref in self.weak_refs.copy():
            if weak_ref() is None:
                dead_refs.append((ref_id, weak_ref))

        for ref_id, weak_ref in dead_refs:
            self.weak_refs.discard((ref_id, weak_ref))

        # If memory is high, clear some caches
        current_memory = self._get_memory_usage()
        if current_memory > self._memory_threshold:
            # Clear half of the chart cache
            chart_keys = list(self.chart_cache.keys())
            for key in chart_keys[:len(chart_keys)//2]:
                del self.chart_cache[key]

            # Clear half of the matrix cache
            matrix_keys = list(self.matrix_cache.keys())
            for key in matrix_keys[:len(matrix_keys)//2]:
                del self.matrix_cache[key]

        # Force garbage collection
        gc.collect()

    def _get_memory_usage(self) -> float:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # Fallback: rough estimate
            return len(gc.get_objects()) * 1000  # Rough approximation

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            'chart_cache_size': len(self.chart_cache),
            'matrix_cache_size': len(self.matrix_cache),
            'weak_refs_count': len(self.weak_refs),
            'memory_usage_mb': self._get_memory_usage() / (1024 * 1024),
            'memory_threshold_mb': self._memory_threshold / (1024 * 1024)
        }


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def reset_memory_manager():
    """Reset the global memory manager instance."""
    global _memory_manager
    _memory_manager = None


def log_performance_metrics():
    """Log current performance metrics."""
    optimizer = get_performance_optimizer()
    report = optimizer.get_performance_report()

    print("=== Performance Report ===")
    print(f"Optimization Enabled: {report['optimization_enabled']}")
    print(".2f")
    print(".1%")
    print(f"Memory Trend: {report['metrics']['memory_trend']}")
    print(f"Dirty Components: {report['dirty_components']}")
    print(f"Cached Renders: {report['cached_renders']}")
    print(f"Cached Data: {report['cached_data']}")
    print(f"Lazy Components: {report['lazy_components']}")

    if report['suggestions']:
        print("\nOptimization Suggestions:")
        for suggestion in report['suggestions']:
            print(f"  • {suggestion}")

    print("=" * 25)


def log_memory_metrics():
    """Log detailed memory usage metrics."""
    try:
        memory_manager = get_memory_manager()
        memory_stats = memory_manager.get_memory_stats()

        print("=== Memory Report ===")
        print(".1f")
        print(f"Chart Cache: {memory_stats['chart_cache_size']} items")
        print(f"Matrix Cache: {memory_stats['matrix_cache_size']} items")
        print(f"Weak References: {memory_stats['weak_refs_count']} refs")
        print(".1f")

        # Memory usage trend
        memory_mb = memory_stats['memory_usage_mb']
        if memory_mb > 500:
            print("⚠️  HIGH MEMORY USAGE - Consider optimization")
        elif memory_mb > 200:
            print("⚡ MODERATE MEMORY USAGE")
        else:
            print("✅ LOW MEMORY USAGE")

        print("=" * 25)

    except ImportError:
        print("Memory manager not available - install requirements for detailed memory monitoring")


def auto_memory_optimization():
    """
    Automatically optimize memory usage based on current conditions.

    This function should be called periodically during long-running sessions
    to prevent memory leaks and optimize performance.
    """
    try:
        memory_manager = get_memory_manager()
        memory_stats = memory_manager.get_memory_stats()

        # If memory usage is high, trigger optimization
        if memory_stats['memory_usage_mb'] > memory_stats['memory_threshold_mb']:
            print("🔧 Auto-optimizing memory usage...")
            memory_manager.optimize_memory_usage()

            # Also optimize performance caches
            optimizer = get_performance_optimizer()
            optimizer.optimize_memory()

            print("✅ Memory optimization complete")

    except ImportError:
        # Fallback: basic garbage collection
        gc.collect()


def safe_memory_operation(operation: Callable, operation_name: str = "operation"):
    """
    Execute an operation with memory monitoring and cleanup.

    Args:
        operation: Function to execute
        operation_name: Name of the operation for logging

    Returns:
        Result of the operation
    """
    try:
        # Get initial memory stats
        initial_memory = get_memory_usage_report()

        # Execute operation
        result = operation()

        # Get final memory stats
        final_memory = get_memory_usage_report()

        # Log significant memory changes
        memory_diff = final_memory.get('rss_mb', 0) - initial_memory.get('rss_mb', 0)
        if abs(memory_diff) > 10:  # More than 10MB change
            print(".1f")

        return result

    except Exception as e:
        print(f"❌ Error in {operation_name}: {e}")
        # Attempt cleanup on error
        gc.collect()
        raise


# Integration with Textual framework
def setup_memory_monitoring(app):
    """
    Setup automatic memory monitoring for a Textual app.

    Args:
        app: Textual app instance
    """
    def memory_check():
        """Periodic memory check."""
        try:
            auto_memory_optimization()
        except Exception as e:
            print(f"Memory monitoring error: {e}")

    # Setup periodic memory checks (every 5 minutes)
    import asyncio
    if hasattr(asyncio, 'create_task'):
        asyncio.create_task(_periodic_memory_check(300))  # 5 minutes


async def _periodic_memory_check(interval: int = 300):
    """Periodic memory monitoring task."""
    while True:
        await asyncio.sleep(interval)
        try:
            auto_memory_optimization()
        except Exception as e:
            # Don't crash the app on memory monitoring errors
            print(f"Memory monitoring error: {e}")


# Utility function for memory-aware chart operations
def memory_efficient_chart_operation(chart_func: Callable, *args, **kwargs):
    """
    Execute a chart operation with memory management.

    Args:
        chart_func: Chart operation function
        *args: Arguments for the function
        **kwargs: Keyword arguments

    Returns:
        Result of the chart operation
    """
    def operation():
        return chart_func(*args, **kwargs)

    return safe_memory_operation(operation, f"chart_operation_{chart_func.__name__}")
