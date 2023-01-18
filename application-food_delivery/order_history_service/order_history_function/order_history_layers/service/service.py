from __future__ import annotations  # classの依存関係の許可

import dataclasses
from typing import Optional

from order_history_layers.model import order_history_model
from order_history_layers.service import events
from order_history_layers.service import commands
# from order_history_layers.service.domain_event_envelope import DomainEventEnvelope
from order_history_layers.service.events import DomainEventEnvelope


class OrderHistoryService:

    def __init__(self, order_history_dao) -> None:
        self.order_history_dao = order_history_dao

    # ------------------------------------------------------------
    # Order Service Event
    # ------------------------------------------------------------
    def create_order(self, event: events.OrderCreated):
        print("create_order:")

        order = order_history_model.Order.create_order(
            order_id=event.order_id,
            order_details=event.order_details,
            delivery_information=event.delivery_information)

        # order_event_id: 冪等性の対応
        self.order_history_dao.save(order, order_event_id=event.event_id)

    """ 注:
        Order History ServiceはDDDではないのでdomain layerは無い。
        service layerから直接DynamoDBを操作する。    
    """
    def update_order_state(self, event: events.DomainEventEnvelope):
        self.order_history_dao.update_order_state(event, order_event_id=event.event_id)

    def update_delivery_state(self, event: events.DomainEventEnvelope):
        self.order_history_dao.update_delivery_state(event, delivery_event_id=event.event_id)
        # Todo:Test方法
        #  1. PostMan: Order:CreateOrder -> order_id
        #  2. PostMan: Kitchen:AcceptTicket (order_id)
        #  3. PostMan: Delivery:CourierPickedup (order_id)

    # /orders/{order_id} GET
    def get_order(self, cmd: commands.GetOrder) -> order_history_model.Order:
        order = self.order_history_dao.find_by_id(cmd.order_id)
        return order
        # Todo:Test方法
        #  1. PostMan: Order:CreateOrder -> order_id
        #  2. PostMan: Kitchen:AcceptTicket (order_id)
        #  3. PostMan: Order:CancelOrder (order_id)
        #  4. PostMan: OrderHistory:GetOrder (order_id)

    # /orders GET
    def get_order_history(self, cmd: commands.GetOrders) -> list[order_history_model.Order]:
        orders = self.order_history_dao.find_order_history(
            cmd.consumer_id, self.order_history_dao.OrderHistoryFilter())
        return orders
        # Todo:Test方法
        #  1. PostMan: Order:CreateOrder -> order_id
        #  2. PostMan: Kitchen:AcceptTicket (order_id)
        #  3. PostMan: Order:CancelOrder (order_id)
        #  4. PostMan: OrderHistory:GetOrderHistory (consumer_id: 認証から取得)
