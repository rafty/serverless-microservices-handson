import dataclasses
import datetime
import random
from delivery_layer.domain import delivery_model
from delivery_layer.domain import restaurant_model
from delivery_layer.domain import courier_model
from delivery_layer.service import events
from delivery_layer.service import commands
from delivery_layer.common import exception as ex


class DeliveryService:

    def __init__(self, delivery_repo, courier_repo, restaurant_repo):
        self.delivery_repo = delivery_repo
        self.courier_repo = courier_repo
        self.restaurant_repo = restaurant_repo

    # ---------------------------------------------------
    # from Restaurant Service
    # ---------------------------------------------------
    # from RestaurantCreated
    def create_replica_restaurant(self, event: events.RestaurantCreated):
        restaurant = restaurant_model.Restaurant(restaurant_id=event.restaurant_id,
                                                 restaurant_name=event.restaurant_name,
                                                 restaurant_address=event.restaurant_address)
        self.restaurant_repo.save(restaurant=restaurant)
        return None

    # ---------------------------------------------
    # Courier
    # ---------------------------------------------
    # path="/couriers/{courier_id}/availability", method=RequestMethod.POST)
    def update_courier_availability(self, cmd: commands.CourierAvailability):
        # Todo: sampleはなぜTransactionなのか？
        #  -> 以下の処理を一発のDynamoDB APIで呼び出す。
        courier = None
        if cmd.available:
            courier = self._note_available_courier(cmd.courier_id)
        else:
            courier = self._note_unavailable_courier(cmd.courier_id)
        return courier

    def _note_available_courier(self, courier_id):
        courier = self._find_or_create_courier(courier_id)
        courier = courier.note_available()
        self.courier_repo.save(courier)
        return courier

    def _note_unavailable_courier(self, courier_id):
        courier = self._find_or_create_courier(courier_id)
        courier = courier.note_unavailable()
        self.courier_repo.save(courier)
        return courier

    def _find_or_create_courier(self, courier_id):
        courier = courier_model.Courier.create(courier_id)
        try:
            self.courier_repo.create(courier)
            return courier
        except ex.CourierAlreadyExists:
            courier_ = self.courier_repo.find_by_id(courier_id)
            return courier_

    def _find_all_available_courier(self):
        couriers = self.courier_repo.find_available()
        pass

    # -----------------------------------------------------
    # Delivery
    # -----------------------------------------------------
    # [注意] order_id, ticket_id, delivery_idは同じもの

    # ---
    # from OrderCreated Event
    def create_delivery(self, event: events.OrderCreated):

        restaurant = self.restaurant_repo.find_by_id(restaurant_id=event.restaurant_id)
        delivery = delivery_model.Delivery.create(delivery_id=event.order_id,  # order_idとdelivery_idは同じもの
                                                  delivery_address=event.delivery_address,
                                                  restaurant_id=event.restaurant_id,
                                                  pickup_address=restaurant.restaurant_address)
        self.delivery_repo.save(delivery)
        return delivery

    # ---
    # from TicketAccepted Event
    def schedule_delivery(self, event: events.TicketAccepted):

        """  Todo: Stupid implementation
                ここの処理は、Application Service LayerからDomainServiceに持っていきたい。
                    1. 該当deliveryとすべてのcourierをrepoから取得する
                    2. xxxDomainService(deliverlry, all_couriers)
                    3. xxxDomainService.schedule()
        """

        delivery = self.delivery_repo.find_by_id(delivery_id=event.ticket_id)

        couriers: list[courier_model] = self.courier_repo.find_all_available_courier()
        courier = random.choice(couriers)

        courier.add_action(courier_model.Action.make_pickup(
            delivery_id=delivery.delivery_id,
            pickup_address=delivery.pickup_address,
            pickup_time=event.ready_by
        ))
        courier.add_action(courier_model.Action.make_dropoff(
            delivery_id=delivery.delivery_id,
            delivery_address=delivery.delivery_address,
            delivery_time=event.ready_by+datetime.timedelta(minutes=30)
        ))
        self.courier_repo.save(courier)

        delivery_ = delivery.schedule(ready_by=event.ready_by, assigned_courier=courier.courier_id)
        self.delivery_repo.save(delivery_)
        return delivery_  # return delivery for Debug

    # ---
    # from TicketCancelled Event @KitchenService
    def cancel_delivery(self, event: events.TicketCancelled):
        # Todo:Test方法
        #  1. PostMan: Order:CreateOrder -> order_id
        #  2. PostMan: Kitchen:AcceptTicket (order_id)
        #  3. PostMan: Order:CancelOrder (order_id)

        print(f'cancel_delivery(): event: {event}')
        delivery: delivery_model.Delivery = self.delivery_repo.find_by_id(delivery_id=event.ticket_id)

        print(f'delivery.assigned_courier: {delivery.assigned_courier}')

        if delivery.assigned_courier:
            courier: courier_model.Courier = self.courier_repo.find_by_id(
                                                            courier_id=delivery.assigned_courier)
            courier_ = courier.cancel_delivery(delivery_id=delivery.delivery_id)
            self.courier_repo.save(courier_)

        delivery_ = delivery.cancel()
        self.delivery_repo.save(delivery_)

    def _find_delivery_by_id(self, delivery_id):
        return self.delivery_repo.find_by_id(delivery_id)

    # Todo: path="/deliveries/{deliveryId}", method= RequestMethod.GET)
    # Todo: ここはなぜTransactionなのか？
    # @staticmethod
    # def get_delivery_info():
    #     pass
    #
    # @staticmethod
    # def _makeDeliveryStatus():
    #     pass
    #
    # @staticmethod
    # def _makeActionInfo():
    #     pass
