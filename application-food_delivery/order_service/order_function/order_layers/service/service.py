from __future__ import annotations  # classの依存関係の許可
from order_layers.domain import order_model
from order_layers.domain import restaurant_model
from order_layers.service import events
from order_layers.service import commands
from order_layers.domain import order_domain_events
from order_layers.service.domain_event_envelope import DomainEventEnvelope


class OrderService:

    def __init__(self, order_repo, order_event_repo, restaurant_replica_repo) -> None:
        self.order_repo = order_repo
        self.order_event_repo = order_event_repo
        self.restaurant_replica_repo = restaurant_replica_repo

    # ------------------------------------------------------------
    # for Restaurant Service Events
    # ------------------------------------------------------------

    # execute from event
    def create_replica_restaurant(self, event: events.RestaurantCreated):
        restaurant = restaurant_model.Restaurant(event.restaurant_id,
                                                 event.restaurant_name,
                                                 event.menu_items)

        self.restaurant_replica_repo.save(restaurant, event.event_id, event.timestamp)

    # Todo: 必要無い？
    # def _find_restaurant_by_id(self, restaurant_id) -> restaurant_model.Restaurant:
    #     restaurant = self.restaurant_replica_repo.find_by_id(restaurant_id)
    #     if restaurant is None:
    #         raise exception.InvalidName(f'Invalid id {restaurant_id}')
    #     return restaurant

    # # execute from event
    # def revise_menu(self, restaurant_id, menu_items):
    #     restaurant = self.restaurant_replica_repo.findById(restaurant_id)
    #     restaurant.revise_menu(menu_items)
    #     return restaurant

    # ------------------------------------------------------------
    # for Order REST
    # ------------------------------------------------------------

    # POST /orders
    def create_order(self, cmd: commands.CreateOrder) -> order_model.Order:  # test目的でリターンを返す
        print("create_order:")

        restaurant = self.restaurant_replica_repo.find_by_id(cmd.restaurant_id)
        order_line_items = self._make_order_line_items(cmd.order_line_items, restaurant)

        order, domain_event = order_model.Order.create_order(
            consumer_id=cmd.consumer_id,
            restaurant=restaurant,
            delivery_information=cmd.delivery_information,
            order_line_items=order_line_items)

        # Todo: 1. Sagaを実行するためorder_event_repo.save()をトランザクションで実行する
        # Todo: 2. 並列処理は楽観ロックの実装をする。
        self.order_repo.save(order)

        event_id = self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        # Todo: event_idの理由:
        #  CQRSのレイテンシーがあるため、REST API Clientがpollingするidとして使えるようにリターンする。
        #  現段階ではREST APIのresultには入れてない。
        return order

    @staticmethod
    def _make_order_line_items(
            order_line_items: list[commands.OrderRequestLineItems],
            restaurant: restaurant_model.Restaurant) -> order_model.OrderLineItems:

        print("_make_order_line_items:")

        order_line_item_list = [
            order_model.OrderLineItem(
                menu_id=item.menu_id,
                name=restaurant.find_menu_item(item.menu_id).menu_name,
                price=restaurant.find_menu_item(item.menu_id).price,
                quantity=item.quantity)
            for item in order_line_items]

        return order_model.OrderLineItems(line_items=order_line_item_list)

    def find_order_by_id(self, cmd: commands.GetOrder) -> order_model.Order:
        order = self.order_repo.find_by_id(cmd.order_id)
        return order

    # Create Order Saga
    def approve_order(self, cmd: commands.ApproveOrder):
        """ Todo 1: ここでは楽観ロックすること。
             　　　Orderは複数Userが編集する前提。
            Todo 2: Outboxパターンを行うため、order.save()とorder_domain_event.save()を一つの関数にして、
                    Transaction処理を行うこと。
            Todo 3: Domain Event - EventIDシーケンシャル番号を持つこと。Timestampを持つこと。変更を加えたUserIDを持つこと。
        """
        order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.note_approved()

        self.order_repo.save(order_)
        self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return
    # Todo: 楽観ロックの対応
    # def approve_order(order_id, order_repo, order_aggregate_event_pub):
    #     # Orderを承認する
    #     # OrderService.update_order(
    #                   order_id, model.Order.note_approved, order_repo, order_aggregate_event_pub)
    #     # meterRegistry.ifPresent()  # Todo: meterRegistry.ifPresentって何？
    #     """
    #     Todo: ステータス変更ならAggregate Rootのみ更新するようにしたい。
    #     DDDのRepositoryPattern, AggregatePatternでは
    #     1. RepositoryからAggregateを取得(Get)
    #     2. Aggregateの処理(domainのビジネスロジックの処理) (Aggregateの変更)
    #     3. 変更されたAggregateをRepositoryに保存する
    #     4. これらは楽観ロック(lock_version)で排他制御を行う
    #     5. 書き込みの際、複数レコードを更新する場合は、トランザクションWriteを使う。
    #     6. lock_versionはAggregateに保持する
    #     7. TransactionWriteでは100Itemまでしか対応できないことに注意
    #     8. 100Item以上の場合は、複数のTransactionWriteを呼び出す。(AWS Bestpractice)
    #     (注)とりあえずRDBのRepositoryPatternのように対応してるが、将来は変更部分だけ更新するように対応する。
    #     (案)取得はAggregateのすべてを取得し、書き込みは変更部分だけ実施する。
    #     """
    #
    #     """ 楽観ロック Optimistic Lock """
    #     """ Repository Pattern: Aggregate全取得 """
    #     while True:  # 楽観ロックで割り込みがあればリトライ
    #         try:
    #             order = order_repo.find_by_id(order_id)  # Aggregate全取得
    #             current_lock_version = order.lock_version  # version for Optimistic Lock
    #             events = order.note_approved()  # Aggregate処理
    #             order.lock_version += 1  # version for Optimistic Lock
    #             updated_response = order_repo.update(order, current_lock_version)  # Aggregate全保存
    #             break
    #         except dx.ConditionalCheckFailedException as e:
    #             print(f'ConditionalCheckFailedException. Retrying again...')
    #
    #     # order_aggregate_event_pub.publish(events)  Todo: 対処せよ
    #
    #     # return
    #     return updated_response  # fot debug

    # POST orders/{orderId}/cancel -> Cancel Order Saga Start
    def start_cancel_order_saga(self, cmd: commands.CancelOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)

        # Todo: Sagaの開始がOrderStateに反映させないため、
        #  ここでSagaを開始するEventを作成する。
        domain_event = order_domain_events.CancelOrderSagaRequested(
                                                            order_id=order.order_id,
                                                            consumer_id=order.consumer_id,
                                                            order_total=order.get_order_total())
        self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return

    # Cancel Order Saga member
    def begin_cancel(self, cmd: commands.BeginCancelOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.cancel()
        self.order_repo.save(order_)
        if domain_event:
            self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return

    def confirm_cancel(self, cmd: commands.ConfirmCancelOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.note_canceled()
        self.order_repo.save(order_)
        if domain_event:
            self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return

    def undo_cancel(self, cmd: commands.UndoBeginCancelOrder):
        # Cancel Order Saga の補償トランザクション
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.undo_pending_cancel()
        self.order_repo.save(order_)
        if domain_event:
            self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return

    def reject_order(self, cmd: commands.RejectOrder):
        order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.note_rejected()
        self.order_repo.save(order_)
        self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return

    # ---------------------------------------------
    # Revise Order Saga　Start
    # ---------------------------------------------

    # path = "orders/{orderId}/revise"
    def start_revise_order_saga(self, cmd: commands.ReviseOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        #  Sagaの開始がOrderStateに反映させないため、
        #  Application Service LayerでSagaを開始するEventを作成している。
        #  Order Service以外のParameterがあるので、
        #  Order ServiceのCreateOrderからSagaを起動するのは好ましくない。
        domain_event = order_domain_events.ReviseOrderSagaRequested(
                                                                order_id=order.order_id,
                                                                consumer_id=order.consumer_id,
                                                                order_revision=cmd.order_revision)
        self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return order

    # from Revise Order Saga
    def begin_revise_order(self, cmd: commands.BeginReviseOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        order_, line_item_quantity_change, domain_event = order.revise(cmd.order_revision)
        self.order_repo.save(order_)
        self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return line_item_quantity_change  # new_order_totalをAccount Serviceに伝える必要がある

    def confirm_revise_order(self, cmd: commands.ConfirmReviseOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.confirm_revision(order_revision=cmd.order_revision)
        self.order_repo.save(order_)
        self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return order

    # 補償トランザクション
    def undo_begin_revise_order(self, cmd: commands.UndoBeginReviseOrder):
        order: order_model.Order = self.order_repo.find_by_id(cmd.order_id)
        order_, domain_event = order.undo_revise_order()
        self.order_repo.save(order_)
        if domain_event:
            self.order_event_repo.save(DomainEventEnvelope.wrap(domain_event))
        return

    # def confirm_change_line_item_quantity(order_id, order_revision):
    #
    #     order = order_repo.find_by_id(order_id)
    #     events = order.confirm_revision(order_revision)
    #     order_aggregate_event_pub.publish(order, events)
    #     return order
    #
    # def note_reversing_authorization(order_id):
    #
    #     raise exception.UnsupportedOperationException(f'{order_id}')
    #
    # def undo_pending_revision(order_id):
    #
    #     OrderService.update_order(
    #               order_id, model.Order.reject_revision, order_repo, order_aggregate_event_pub)
