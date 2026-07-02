"""Foundation Event System — DomainEvent e IntegrationEvent."""

from foundation.events.domain_event import DomainEvent
from foundation.events.integration_event import IntegrationEvent

__all__ = [
    "DomainEvent",
    "IntegrationEvent",
]
