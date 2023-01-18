#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.sample_service_stack import SampleServiceStack
from stacks.order_service_stack import OrderServiceStack
from stacks.restaurant_service_stack import RestaurantServiceStack
from stacks.consumer_service_stack import ConsumerServiceStack
from stacks.kitchen_service_stack import KitchenServiceStack
from stacks.account_service_stack import AccountServiceStack
from stacks.delivery_service_stack import DeliveryServiceStack
from stacks.order_history_service_stack import OrderHistoryServiceStack


env = cdk.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]),
)

app = cdk.App()

SampleServiceStack(app, 'SampleServiceStack', env=env)  # Todo: 削除予定

# -----------------------------------------------------------
# Restaurant Service
# -----------------------------------------------------------
restaurant_service = RestaurantServiceStack(app, "RestaurantServiceStack", env=env)

# -----------------------------------------------------------
# Consumer Service
# -----------------------------------------------------------
consumer_service = ConsumerServiceStack(app, "ConsumerServiceStack", env=env)

# -----------------------------------------------------------
# Kitchen Service
# -----------------------------------------------------------
kitchen_service = KitchenServiceStack(app, "KitchenServiceStack", env=env)
kitchen_service.add_dependency(restaurant_service)

# -----------------------------------------------------------
# Account Service
# -----------------------------------------------------------
account_service = AccountServiceStack(app, "AccountServiceStack", env=env)

# -----------------------------------------------------------
# Order Service
# -----------------------------------------------------------
order_service = OrderServiceStack(app, "OrderServiceStack", env=env)
order_service.add_dependency(restaurant_service)
order_service.add_dependency(consumer_service)
order_service.add_dependency(kitchen_service)

# -----------------------------------------------------------
# Delivery Service
# -----------------------------------------------------------
delivery_service = DeliveryServiceStack(app, "DeliveryServiceStack", env=env)
delivery_service.add_dependency(order_service)


# -----------------------------------------------------------
# Order History Service
# -----------------------------------------------------------
order_history_service = OrderHistoryServiceStack(app, "OrderHistoryServiceStack", env=env)
order_history_service.add_dependency(account_service)
order_history_service.add_dependency(order_service)
order_history_service.add_dependency(kitchen_service)
order_history_service.add_dependency(delivery_service)


app.synth()
