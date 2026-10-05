"""Lightweight in-memory event bus for decoupling subsystem notifications."""

from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """Publish-subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[str, Any], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[str, Any], None]) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, data: Any = None) -> None:
        if event_name in self._subscribers:
            for handler in self._subscribers[event_name]:
                try:
                    handler(event_name, data)
                except Exception as ex:
                    logger.error(f"Error handling event {event_name}: {ex}", exc_info=True)


# Global singleton instance
bus = EventBus()
