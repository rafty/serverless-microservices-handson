from __future__ import annotations  # classの依存関係の許可
import dataclasses
import datetime
from account_layers.domain import domain_events


@dataclasses.dataclass(frozen=True)
class DomainEventEnvelope:
    aggregate: str  # ACCOUNT
    aggregate_id: str  # account_id
    event_type: str  # AccountCreated
    event_id: int  # 1, 2, 3... Sequential
    timestamp: str  # ISO 8601: 2022-11-30T05:00:30.001000Z
    domain_event: domain_events.DomainEvent

    @classmethod
    def wrap(cls, event: domain_events.DomainEvent):

        print(f'event: {event}')

        return DomainEventEnvelope(
            aggregate='ACCOUNT',
            aggregate_id=event.account_id,
            event_type=event.__class__.__name__,
            event_id=None,  # Repositoryで対応
            timestamp=None,  # Repositoryで対応
            domain_event=event)
