from __future__ import annotations
import dataclasses
import decimal
import uuid
import json
from consumer_layers.common import common
from consumer_layers.domain import domain_events


class Consumer:
    """
    DynamoDB Table Construction
        PK: CONSUMER#{consumer_id}
        SK: METADATA#{consumer_id}
        name: {
            "first_name": "Takashi",
            "last_name": "Yagita",
        }
    """

    def __init__(self,
                 name: common.PersonName,
                 consumer_id: int):

        self.consumer_id: int = consumer_id
        self.name: common.PersonName = name

    @classmethod
    def from_dict(cls, d: dict):
        d['name'] = common.PersonName.from_dict(d['name'])
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Consumer):
                return o.__dict__
            if isinstance(o, common.PersonName):
                return dataclasses.asdict(o)
            if isinstance(o, decimal.Decimal):
                return o  # Decimalのまま返す
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d

    @classmethod
    def create(cls, name: common.PersonName, consumer_id: int):
        consumer = cls(name=name, consumer_id=consumer_id)
        event = domain_events.ConsumerCreated(consumer_id=consumer.consumer_id,
                                             name=consumer.name)
        return consumer, event

    def validate_order_by_consumer(self, order_total: common.Money):

        # Todo: implement some business logic

        # Todo: とりあえず固定でエラーを返していたのできちんとロジックを実装すること。
        # raise exceptions.ConsumerVerificationFailedException(
        #     f'ConsumerVerificationFailed: consumer_id: {self.consumer_id}')

        return True
