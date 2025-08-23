"""
Global state management for Holdem CLI application.

This module provides centralized state management across all screens
and components, ensuring consistent data flow and user experience.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json


class AppState:
    """Global application state manager."""

    def __init__(self):
        self._state = {
            # User profile
            'current_profile': 'default',
            'profiles': [],

            # Current chart
            'current_chart': None,
            'chart_history': [],

            # Quiz state
            'quiz_session': None,
            'quiz_history': [],

            # Simulation state
            'simulation_history': [],

            # UI state
            'theme': 'default',
            'notifications': [],

            # Settings
            'settings': {
                'auto_save': True,
                'max_history': 100,
                'default_iterations': 25000,
                'default_ai_level': 'easy'
            }
        }
        self._listeners: Dict[str, list] = {}
        self._history = []

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any, notify: bool = True) -> None:
        """Set a state value and optionally notify listeners."""
        old_value = self._state.get(key)

        # Save to history for undo functionality
        if old_value != value:
            self._history.append({
                'timestamp': datetime.now(),
                'key': key,
                'old_value': old_value,
                'new_value': value
            })

            # Limit history size
            max_history = self._state['settings']['max_history']
            if len(self._history) > max_history:
                self._history = self._history[-max_history:]

        self._state[key] = value

        if notify:
            self._notify_listeners(key, old_value, value)

    def update(self, updates: Dict[str, Any], notify: bool = True) -> None:
        """Update multiple state values at once."""
        for key, value in updates.items():
            self.set(key, value, notify=False)

        if notify:
            for key, value in updates.items():
                old_value = self._state.get(key)
                self._notify_listeners(key, old_value, value)

    def subscribe(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """Subscribe to state changes for a specific key."""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """Unsubscribe from state changes."""
        if key in self._listeners and callback in self._listeners[key]:
            self._listeners[key].remove(callback)

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify listeners about state changes."""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    print(f"Error in state listener callback: {e}")

    def undo(self) -> bool:
        """Undo the last state change."""
        if not self._history:
            return False

        last_change = self._history.pop()
        self.set(last_change['key'], last_change['old_value'], notify=True)
        return True

    def get_history(self) -> list:
        """Get the state change history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the state change history."""
        self._history.clear()

    def add_notification(self, message: str, severity: str = 'info', timeout: int = 5) -> None:
        """Add a notification to the state."""
        notification = {
            'id': len(self._state['notifications']),
            'message': message,
            'severity': severity,
            'timeout': timeout,
            'timestamp': datetime.now()
        }
        self._state['notifications'].append(notification)
        self._notify_listeners('notifications', None, self._state['notifications'])

    def clear_notifications(self) -> None:
        """Clear all notifications."""
        self._state['notifications'].clear()
        self._notify_listeners('notifications', None, [])

    def get_recent_notifications(self, limit: int = 10) -> list:
        """Get recent notifications."""
        return self._state['notifications'][-limit:] if self._state['notifications'] else []

    def save_state(self, filename: Optional[str] = None) -> bool:
        """Save current state to file."""
        try:
            if not filename:
                filename = f"holdem_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Create a serializable version of the state
            serializable_state = {}
            for key, value in self._state.items():
                try:
                    # Convert datetime objects to strings
                    if isinstance(value, datetime):
                        serializable_state[key] = value.isoformat()
                    elif isinstance(value, list):
                        serializable_state[key] = [
                            item.isoformat() if isinstance(item, datetime) else item
                            for item in value
                        ]
                    else:
                        json.dumps(value)  # Test if serializable
                        serializable_state[key] = value
                except (TypeError, ValueError):
                    # Skip non-serializable values
                    continue

            with open(filename, 'w') as f:
                json.dump(serializable_state, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self, filename: str) -> bool:
        """Load state from file."""
        try:
            with open(filename, 'r') as f:
                state_data = json.load(f)

            # Update state with loaded data
            for key, value in state_data.items():
                if key in self._state:
                    self.set(key, value, notify=False)

            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get application usage statistics."""
        return {
            'total_profiles': len(self._state.get('profiles', [])),
            'total_charts': len(self._state.get('chart_history', [])),
            'total_quizzes': len(self._state.get('quiz_history', [])),
            'total_simulations': len(self._state.get('simulation_history', [])),
            'state_changes': len(self._history),
            'notifications_sent': len(self._state.get('notifications', [])),
            'current_theme': self._state.get('theme', 'default')
        }


# Global state instance
_global_state = AppState()


def get_app_state() -> AppState:
    """Get the global application state instance."""
    return _global_state


def reset_app_state() -> None:
    """Reset the global application state."""
    global _global_state
    _global_state = AppState()

