```mermaid
classDiagram

RestaurantCreated_Restaurant~Event~ *-- MenuItem_Restaurant
RestaurantCreated_Order <|-- RestaurantCreated_Restaurant~Event~
RestaurantCreated_Order *-- MenuItem_Order

    class RestaurantCreated_Restaurant{
        restaurant_id
        restaurant_name
        restaurant_address
        menu_items
    }
    class MenuItem_Restaurant{
        menu_id
        menu_name
        price
    }

    class RestaurantCreated_Order{
        restaurant_id
        restaurant_name
        menu_items
    }
    class MenuItem_Order{
        menu_id
        menu_name
        price
    }


```


```mermaid
classDiagram
    OrderServiceRestaurantRepo <|-- RestaurantCreatedEvent
    CreateOrderSaga <|-- OrderDetails
    CreateOrderRequest <|-- order_line_items
    menu_items_OrderRepo <|-- OrderServiceRestaurantRepo 
    menu_items_RestaurantEvent  <|-- RestaurantCreatedEvent
    
    class RestaurantCreatedEvent{
        restaurant_id(必要)
        restaurant_name(使わない？)
        restaurant_address(必要)
        menu_items(master)
    }
    class menu_items_RestaurantEvent{
        menu_id
        menu_name
        menu_price
    }
    
    
    class OrderServiceRestaurantRepo{
        restaurant_id(無し)
        restaurant_name(使わない？)
        restaurant_address(Orderでは使わない)
        menu_items(orderRepo)
    }
    class menu_items_OrderRepo{
        menu_id
        menu_name
        menu_price
    }


    ここから    

    class CreateOrderRequest{
        consumer_id
        restaurant_id
        order_line_items
        delivery_informaition
    }
    class order_line_items{
        menu_id
        quantity
    }
    class delivery_informaition{
        
    
    }
    
    
    class makeOrderLineItems{
        quantity : from Req
        menu_id from Req
        menu_name : from RestaurantRepo
        menu_price : from RestaurantRepo
    }
    class saveOrder{
        order_id
        version
        state
        consumer_id
        restaurant_id
        order_line_items
        delivery_informaition
        order_minimun
    }
    class OrderCreatedEvent{
        consumer_id
        restaurant_id
        order_line_items
        order_total
        
        delivery_informaition.address
        restaurant_name
    }
    class OrderDetails{
        consumer_id
        restaurant_id
        order_line_items
        order_total
    }
    class CreateOrderSaga{
        order_id
        order_details
    }
    

```





```
this.sagaDefinition =
         step()
          .withCompensation(orderService.reject, CreateOrderSagaState::makeRejectOrderCommand)
        .step()
          .invokeParticipant(consumerService.validateOrder, CreateOrderSagaState::makeValidateOrderByConsumerCommand)  // Todo: ①顧客のチェック (顧客サービス)
        .step()
          .invokeParticipant(kitchenService.create, CreateOrderSagaState::makeCreateTicketCommand)  // Todo: ② チケットの作成 (キッチンサービス)
          .onReply(CreateTicketReply.class, CreateOrderSagaState::handleCreateTicketReply)
          .withCompensation(kitchenService.cancel, CreateOrderSagaState::makeCancelCreateTicketCommand)
        .step()
            .invokeParticipant(accountingService.authorize, CreateOrderSagaState::makeAuthorizeCommand)  // Todo: ③カード承認 (会計サービス)
        .step()
          .invokeParticipant(kitchenService.confirmCreate, CreateOrderSagaState::makeConfirmCreateTicketCommand)  // Todo: ④ キッチンサービス承認
        .step()
          .invokeParticipant(orderService.approve, CreateOrderSagaState::makeApproveOrderCommand)  // Todo: ⑤ オーダ承認 (オーダサービス)
        .build();

```

```
sagaDefinition = step()
        .invokeParticipant(this::beginReviseOrder)
        .onReply(BeginReviseOrderReply.class, this::handleBeginReviseOrderReply)
        .withCompensation(this::undoBeginReviseOrder)
        .step()
        .invokeParticipant(this::beginReviseTicket)
        .withCompensation(this::undoBeginReviseTicket)
        .step()
        .invokeParticipant(this::reviseAuthorization)
        .step()
        .invokeParticipant(this::confirmTicketRevision)
        .step()
        .invokeParticipant(this::confirmOrderRevision)
        .build();
```
```
    sagaDefinition = step()
            .invokeParticipant(this::beginCancel)
            .withCompensation(this::undoBeginCancel)
            .step()
            .invokeParticipant(this::beginCancelTicket)
            .withCompensation(this::undoBeginCancelTicket)
            .step()
            .invokeParticipant(this::reverseAuthorization)
            .step()
            .invokeParticipant(this::confirmTicketCancel)
            .step()
            .invokeParticipant(this::confirmOrderCancel)
            .build();
```

```
REST API

@RequestMapping(path = "/orders")
@RequestMapping(method = RequestMethod.POST)
create(@RequestBody CreateOrderRequest request)
    Order order = orderService.createOrder()


@RequestMapping(path = "/{orderId}", method = RequestMethod.GET)
getOrder(@PathVariable long orderId)

@RequestMapping(path = "/{orderId}/cancel", method = RequestMethod.POST)
public ResponseEntity<GetOrderResponse> cancel(@PathVariable long orderId) {
    Order order = orderService.cancel(orderId);


@RequestMapping(path = "/{orderId}/revise", method = RequestMethod.POST)
public ResponseEntity<GetOrderResponse> revise(@PathVariable long orderId, @RequestBody ReviseOrderRequest request) {
    Order order = orderService.reviseOrder(orderId, new OrderRevision(Optional.empty(), request.getRevisedOrderLineItems()));

```


```
public class OrderEventConsumer {

  private OrderService orderService;

  public OrderEventConsumer(OrderService orderService) {
    this.orderService = orderService;
  }

  public DomainEventHandlers domainEventHandlers() {
    return DomainEventHandlersBuilder
            .forAggregateType("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant")
            .onEvent(RestaurantCreated.class, this::createMenu)
            .onEvent(RestaurantMenuRevised.class, this::reviseMenu)
            .build();
  }

  private void createMenu(DomainEventEnvelope<RestaurantCreated> de) {
    String restaurantIds = de.getAggregateId();
    long id = Long.parseLong(restaurantIds);
    orderService.createMenu(id, de.getEvent().getName(), RestaurantEventMapper.toMenuItems(de.getEvent().getMenu().getMenuItems()));
  }

  public void reviseMenu(DomainEventEnvelope<RestaurantMenuRevised> de) {
    String restaurantIds = de.getAggregateId();
    long id = Long.parseLong(restaurantIds);
    orderService.reviseMenu(id, RestaurantEventMapper.toMenuItems(de.getEvent().getMenu().getMenuItems()));
  }

}
```


```
Service Layer

  public void createMenu(long id, String name, List<MenuItem> menuItems) {
    Restaurant restaurant = new Restaurant(id, name, menuItems);
    restaurantRepository.save(restaurant);
  }

  public void reviseMenu(long id, List<MenuItem> menuItems) {
    restaurantRepository.findById(id).map(restaurant -> {
      List<OrderDomainEvent> events = restaurant.reviseMenu(menuItems);
      return restaurant;
    }).orElseThrow(RuntimeException::new);
  }
```