from __future__ import annotations  # classの依存関係の許可
import dataclasses
from kitchen_layer.domain import kitchen_domain_event


@dataclasses.dataclass(frozen=True)
class DomainEventEnvelope:
    aggregate: str  # TICKET
    aggregate_id: str  # ticket_id
    event_type: str  # TicketCreated, TicketAccepted...
    event_id: int  # 1, 2, 3... Sequential
    timestamp: str  # ISO 8601: 2022-11-30T05:00:30.001000Z
    domain_event: kitchen_domain_event.DomainEvent

    @classmethod
    def wrap(cls, event: kitchen_domain_event.DomainEvent):

        print(f'event: {event}')

        return DomainEventEnvelope(
            aggregate='TICKET',
            aggregate_id=event.ticket_id,
            event_type=event.__class__.__name__,
            event_id=None,  # Repositoryで対応
            timestamp=None,  # Repositoryで対応
            domain_event=event)
