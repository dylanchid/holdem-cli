"""
Render optimization system for TUI widgets.

This module provides advanced rendering optimizations including:
- Dirty checking and incremental updates
- Virtual scrolling for large datasets
- Render batching and coalescing
- Component virtualization
- Render profiling and optimization hints
"""

from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from datetime import datetime, timedelta
import time
import hashlib
from dataclasses import dataclass, field
from weakref import WeakValueDictionary

from ..core.performance import get_performance_optimizer, cached_render


@dataclass
class RenderState:
    """State information for render optimization."""
    last_render_hash: str = ""
    last_render_time: datetime = field(default_factory=datetime.now)
    render_count: int = 0
    is_dirty: bool = True
    dependencies: Set[str] = field(default_factory=set)
    virtual_scroll_position: int = 0
    virtual_scroll_size: int = 100


class RenderOptimizer:
    """
    Advanced render optimization system.

    Features:
    - Dirty checking to avoid unnecessary renders
    - Incremental updates for changed components
    - Virtual scrolling for large datasets
    - Render batching and coalescing
    - Component virtualization
    """

    def __init__(self):
        self.render_states: Dict[str, RenderState] = {}
        self.virtual_components: WeakValueDictionary[str, Any] = WeakValueDictionary()
        self.render_queue: List[Tuple[str, Callable]] = []
        self.batch_size = 10
        self.max_virtual_items = 1000
        self.performance_optimizer = get_performance_optimizer()

    def should_render(self, component_id: str, data_hash: str) -> bool:
        """Check if a component should be re-rendered."""
        if component_id not in self.render_states:
            self.render_states[component_id] = RenderState()

        state = self.render_states[component_id]

        # Always render if marked as dirty
        if state.is_dirty:
            return True

        # Render if data has changed
        if state.last_render_hash != data_hash:
            return True

        # Check if dependencies have changed
        for dep_id in state.dependencies:
            if dep_id in self.render_states and self.render_states[dep_id].is_dirty:
                return True

        return False

    def mark_rendered(self, component_id: str, data_hash: str):
        """Mark a component as rendered with current data hash."""
        if component_id not in self.render_states:
            self.render_states[component_id] = RenderState()

        state = self.render_states[component_id]
        state.last_render_hash = data_hash
        state.last_render_time = datetime.now()
        state.render_count += 1
        state.is_dirty = False

    def mark_dirty(self, component_id: str):
        """Mark a component as dirty (needs re-render)."""
        if component_id not in self.render_states:
            self.render_states[component_id] = RenderState()

        self.render_states[component_id].is_dirty = True

    def add_dependency(self, component_id: str, dependency_id: str):
        """Add a dependency relationship between components."""
        if component_id not in self.render_states:
            self.render_states[component_id] = RenderState()

        self.render_states[component_id].dependencies.add(dependency_id)

    def remove_dependency(self, component_id: str, dependency_id: str):
        """Remove a dependency relationship."""
        if component_id in self.render_states:
            self.render_states[component_id].dependencies.discard(dependency_id)

    def queue_render(self, component_id: str, render_func: Callable):
        """Queue a render operation for batching."""
        self.render_queue.append((component_id, render_func))

        # Process queue if it gets too large
        if len(self.render_queue) >= self.batch_size:
            self.process_render_queue()

    def process_render_queue(self):
        """Process queued render operations."""
        if not self.render_queue:
            return

        start_time = time.time()

        # Group renders by component type for efficiency
        component_renders = {}
        for component_id, render_func in self.render_queue:
            component_type = component_id.split('_')[0] if '_' in component_id else component_id
            if component_type not in component_renders:
                component_renders[component_type] = []
            component_renders[component_type].append((component_id, render_func))

        # Process renders by type
        for component_type, renders in component_renders.items():
            for component_id, render_func in renders:
                try:
                    render_func()
                    self.mark_rendered(component_id, f"queued_{component_id}")
                except Exception as e:
                    print(f"Error rendering {component_id}: {e}")

        # Clear queue
        self.render_queue.clear()

        duration = time.time() - start_time
        self.performance_optimizer.metrics.add_render_time(duration)

    def create_virtual_scroll_view(
        self,
        items: List[Any],
        visible_range: Tuple[int, int],
        item_height: int = 1
    ) -> List[Any]:
        """Create a virtual scroll view for large datasets."""
        start_idx, end_idx = visible_range

        # Ensure valid range
        start_idx = max(0, start_idx)
        end_idx = min(len(items), end_idx)

        # Add some buffer for smooth scrolling
        buffer_size = 5
        buffered_start = max(0, start_idx - buffer_size)
        buffered_end = min(len(items), end_idx + buffer_size)

        return items[buffered_start:buffered_end]

    def optimize_matrix_render(
        self,
        matrix_data: List[List[str]],
        visible_rows: Tuple[int, int],
        visible_cols: Tuple[int, int]
    ) -> List[List[str]]:
        """Optimize matrix rendering for large datasets."""
        row_start, row_end = visible_rows
        col_start, col_end = visible_cols

        # Extract visible portion
        visible_matrix = []
        for i in range(row_start, min(row_end, len(matrix_data))):
            row = matrix_data[i]
            visible_row = row[col_start:min(col_end, len(row))]
            visible_matrix.append(visible_row)

        return visible_matrix

    def create_incremental_update(
        self,
        component_id: str,
        old_data: Any,
        new_data: Any
    ) -> Optional[Dict[str, Any]]:
        """Create incremental update instructions."""
        if old_data is None:
            return None

        # Simple diff-based update
        if isinstance(old_data, list) and isinstance(new_data, list):
            # List diff
            added = [item for item in new_data if item not in old_data]
            removed = [item for item in old_data if item not in new_data]

            if added or removed:
                return {
                    "type": "list_update",
                    "added": added,
                    "removed": removed,
                    "component_id": component_id
                }

        elif isinstance(old_data, dict) and isinstance(new_data, dict):
            # Dict diff
            added_keys = set(new_data.keys()) - set(old_data.keys())
            removed_keys = set(old_data.keys()) - set(new_data.keys())
            changed_keys = set()

            for key in set(old_data.keys()) & set(new_data.keys()):
                if old_data[key] != new_data[key]:
                    changed_keys.add(key)

            if added_keys or removed_keys or changed_keys:
                return {
                    "type": "dict_update",
                    "added": dict((k, new_data[k]) for k in added_keys),
                    "removed": list(removed_keys),
                    "changed": dict((k, new_data[k]) for k in changed_keys),
                    "component_id": component_id
                }

        return None

    def get_render_statistics(self) -> Dict[str, Any]:
        """Get render optimization statistics."""
        total_renders = sum(state.render_count for state in self.render_states.values())
        dirty_components = sum(1 for state in self.render_states.values() if state.is_dirty)

        return {
            "total_components": len(self.render_states),
            "total_renders": total_renders,
            "dirty_components": dirty_components,
            "virtual_components": len(self.virtual_components),
            "queued_renders": len(self.render_queue),
            "average_render_frequency": total_renders / max(1, len(self.render_states))
        }

    def cleanup_unused_states(self):
        """Clean up render states for components that no longer exist."""
        # This would typically be called during garbage collection
        # or when components are destroyed
        pass

    def reset_optimization(self):
        """Reset optimization state."""
        self.render_states.clear()
        self.virtual_components.clear()
        self.render_queue.clear()


# Global render optimizer instance
_render_optimizer: Optional[RenderOptimizer] = None


def get_render_optimizer() -> RenderOptimizer:
    """Get or create the global render optimizer instance."""
    global _render_optimizer
    if _render_optimizer is None:
        _render_optimizer = RenderOptimizer()
    return _render_optimizer


def reset_render_optimizer():
    """Reset the global render optimizer instance."""
    global _render_optimizer
    _render_optimizer = None


# Decorator for optimized rendering
def optimized_render(component_id: str):
    """Decorator to optimize component rendering."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            optimizer = get_render_optimizer()

            # Generate data hash for dirty checking
            data_str = str(args) + str(sorted(kwargs.items()))
            data_hash = hashlib.md5(data_str.encode()).hexdigest()

            # Check if render is needed
            if not optimizer.should_render(component_id, data_hash):
                return None  # Skip render

            # Perform render
            result = func(*args, **kwargs)

            # Mark as rendered
            optimizer.mark_rendered(component_id, data_hash)

            return result

        return wrapper
    return decorator


# Utility functions for render optimization
def create_optimized_matrix_widget(matrix_data: List[List[str]], **kwargs):
    """Create an optimized matrix widget with virtual scrolling."""
    optimizer = get_render_optimizer()

    # Create virtual scroll view
    visible_rows = (0, min(20, len(matrix_data)))  # Show first 20 rows
    visible_cols = (0, min(13, len(matrix_data[0]) if matrix_data else 13))

    optimized_data = optimizer.optimize_matrix_render(
        matrix_data, visible_rows, visible_cols
    )

    # Import here to avoid circular imports
    from ..widgets.matrix_widget import HandMatrixWidget

    # Create widget with optimized data
    widget = HandMatrixWidget(optimized_data, **kwargs)

    # Set up virtual scrolling
    widget.virtual_scroll_enabled = True
    widget.total_rows = len(matrix_data)
    widget.visible_rows = visible_rows

    return widget


def enable_render_optimization():
    """Enable render optimization globally."""
    optimizer = get_render_optimizer()
    optimizer.performance_optimizer.enable_optimization(True)


def disable_render_optimization():
    """Disable render optimization globally."""
    optimizer = get_render_optimizer()
    optimizer.performance_optimizer.enable_optimization(False)


def get_render_optimization_status() -> Dict[str, Any]:
    """Get current render optimization status."""
    optimizer = get_render_optimizer()
    return {
        "optimization_enabled": optimizer.performance_optimizer._optimization_enabled,
        "render_stats": optimizer.get_render_statistics(),
        "performance_metrics": optimizer.performance_optimizer.get_performance_report()
    }
