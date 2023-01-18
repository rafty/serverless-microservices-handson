from __future__ import annotations  # classの依存関係の許可
import dataclasses
import datetime
from delivery_layer.domain import domain_event


@dataclasses.dataclass(frozen=True)
class DomainEventEnvelope:
    aggregate: str  # Order
    aggregate_id: str  # order_id
    event_type: str  # OrderCreated, OrderApproved
    event_id: int  # 1, 2, 3... Sequential
    timestamp: str  # ISO 8601: 2022-11-30T05:00:30.001000Z
    domain_event: domain_event.DomainEvent

    @classmethod
    def wrap(cls, event: domain_event.DomainEvent):

        print(f'event: {event}')

        return DomainEventEnvelope(
            aggregate='DELIVERY',
            aggregate_id=event.delivery_id,
            event_type=event.__class__.__name__,
            event_id=None,  # Repositoryで対応
            timestamp=None,  # Repositoryで対応
            domain_event=event)
