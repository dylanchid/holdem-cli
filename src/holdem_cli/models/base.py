"""
Base data models and mixins for Holdem CLI.

This module provides the foundation for all data models in the application,
including common fields and functionality.
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime, timezone


@dataclass
class BaseModel(ABC):
    """Base class for all data models."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary."""
        # Remove any fields that aren't in the dataclass
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model fields from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self) -> list[str]:
        """Validate model data. Override in subclasses."""
        return []


@dataclass
class TimestampMixin:
    """Mixin providing timestamp fields."""

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class Identifiable:
    """Mixin providing ID field."""

    id: Optional[int] = None

    def has_id(self) -> bool:
        """Check if the model has an ID assigned."""
        return self.id is not None

    def is_new(self) -> bool:
        """Check if this is a new (unsaved) model."""
        return self.id is None


@dataclass
class SoftDeleteMixin:
    """Mixin providing soft delete functionality."""

    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    def soft_delete(self) -> None:
        """Mark the model as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted model."""
        self.is_deleted = False
        self.deleted_at = None

    def is_active(self) -> bool:
        """Check if the model is active (not deleted)."""
        return not self.is_deleted


@dataclass
class VersionedMixin:
    """Mixin providing versioning support."""

    version: int = 1

    def increment_version(self) -> None:
        """Increment the version number."""
        self.version += 1

    def get_version_info(self) -> Dict[str, Any]:
        """Get version information."""
        return {
            'version': self.version,
            'updated_at': getattr(self, 'updated_at', None)
        }


@dataclass
class AuditableMixin:
    """Mixin providing audit trail functionality."""

    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_from_ip: Optional[str] = None
    updated_from_ip: Optional[str] = None

    def set_created_by(self, user_id: str, ip_address: Optional[str] = None) -> None:
        """Set creation audit information."""
        self.created_by = user_id
        if ip_address:
            self.created_from_ip = ip_address

    def set_updated_by(self, user_id: str, ip_address: Optional[str] = None) -> None:
        """Set update audit information."""
        self.updated_by = user_id
        if ip_address:
            self.updated_from_ip = ip_address


@dataclass
class SearchableMixin:
    """Mixin providing search functionality."""

    search_keywords: list[str] = field(default_factory=list)

    def add_search_keyword(self, keyword: str) -> None:
        """Add a search keyword."""
        keyword_lower = keyword.lower().strip()
        if keyword_lower and keyword_lower not in self.search_keywords:
            self.search_keywords.append(keyword_lower)

    def remove_search_keyword(self, keyword: str) -> None:
        """Remove a search keyword."""
        keyword_lower = keyword.lower().strip()
        if keyword_lower in self.search_keywords:
            self.search_keywords.remove(keyword_lower)

    def matches_search(self, query: str) -> bool:
        """Check if the model matches a search query."""
        query_lower = query.lower().strip()
        return any(query_lower in keyword for keyword in self.search_keywords)

    def get_search_score(self, query: str) -> float:
        """Get search relevance score (0.0 to 1.0)."""
        if not self.search_keywords:
            return 0.0

        query_lower = query.lower().strip()
        matches = sum(1 for keyword in self.search_keywords if query_lower in keyword)

        return matches / len(self.search_keywords)


@dataclass
class SerializableMixin:
    """Mixin providing serialization utilities."""

    def to_serializable_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        data = self.to_dict()

        # Convert datetime objects to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        return data

    def to_compact_dict(self) -> Dict[str, Any]:
        """Convert to compact dictionary (excluding None values)."""
        data = self.to_dict()
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_serializable_dict(cls, data: Dict[str, Any]) -> 'SerializableMixin':
        """Create instance from serializable dictionary."""
        # Convert ISO format strings back to datetime objects
        for key, value in data.items():
            if isinstance(value, str) and 'T' in value:  # ISO format datetime
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass  # Leave as string if parsing fails

        return cls.from_dict(data)
