from consumer_layers.domain import consumer_model
from consumer_layers.service import commands
from consumer_layers.common import exceptions


class ConsumerService:

    def __init__(self, consumer_repo, consumer_event_repo):
        self.consumer_repo = consumer_repo
        self.consumer_event_repo = consumer_event_repo

    def create_consumer(self, cmd: commands.CreateConsumer):
        new_consumer_id = self.consumer_repo.get_unique_consumer_id()
        consumer, domain_events = consumer_model.Consumer.create(name=cmd.name,
                                                                 consumer_id=new_consumer_id)
        try:
            self.consumer_repo.save(consumer)
        except exceptions.ConsumerNameAlreadyExists as e:
            raise exceptions.ConsumerNameAlreadyExists(
                f'User name already exist. : {cmd.name.first_name} {cmd.name.last_name}')

        self.consumer_event_repo.save(events=domain_events)

        return consumer

    def get_consumer_by_id(self, cmd: commands.GetConsumer) -> consumer_model.Consumer:
        consumer = self.consumer_repo.find_by_id(cmd.consumer_id)
        return consumer

    def validate_order_for_consumer(self,
                                    cmd: commands.ValidateOrderForConsumer):

        consumer = self.consumer_repo.find_by_id(consumer_id=cmd.consumer_id)
        if consumer:
            resp = consumer.validate_order_by_consumer(cmd.money_total)
        else:
            raise exceptions.ConsumerNotFoundException(
                f'ConsumerNotFound: consumer_id: {cmd.consumer_id}')

        return resp
