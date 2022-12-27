import aws_cdk
from constructs import Construct
from aws_cdk import Duration
from aws_cdk import aws_stepfunctions
from aws_cdk import aws_stepfunctions_tasks


"""
# stepfunction.start_execution()のinput_json

{
  "input": {
    "event_id": "0e439f7e76c742a5997224dd4dbd7890",
    "delivery_information": {
      "delivery_address": {
        "zip": "94612",
        "city": "Oakland",
        "street1": "9 Amazing View",
        "street2": "Soi 8",
        "state": "CA"
      },
      "delivery_time": "2022-11-30T05:00:30.001000Z"
    },
    "order_details": {
      "consumer_id": 4,
      "restaurant_id": 1,
      "order_line_items": [
        {
          "quantity": 3,
          "price": {
            "currency": "JPY",
            "value": 800
          },
          "name": "Curry Rice",
          "menu_id": "000001"
        },
        {
          "quantity": 2,
          "price": {
            "currency": "JPY",
            "value": 1000
          },
          "name": "Hamburger",
          "menu_id": "000002"
        },
        {
          "quantity": 1,
          "price": {
            "currency": "JPY",
            "value": 700
          },
          "name": "Ramen",
          "menu_id": "000003"
        }
      ],
      "order_total": {
        "currency": "JPY",
        "value": 5100
      }
    },
    "order_id": "8a4347b048034e80bfa45a5d70c8f301",
    "channel": "OrderCreated"
  },
  "inputDetails": {
    "truncated": false
  },
  "roleArn": "arn:aws:iam::338456725408:role/OrderServiceStack-CreateOrderSagaConstructorCreate-YLDY0HX8FOFX"
}
"""


class CreateOrderSagaStepFunctions(Construct):

    def __init__(self, scope: Construct, id: str, props: dict) -> None:
        super().__init__(scope, id)
        self.props = props

        # ------------------------------------------------------
        # Saga 参加 function
        # ------------------------------------------------------
        # Order Service Function
        self.approve_order_function = props.get('order_service_function')  # ApproveOrder
        self.reject_order_function = props.get('order_service_function')  # RejectOrder
        # Consumer Service Function
        self.validate_consumer_saga_function = self.get_function_on_cross_stack(
                                                            'ConsumerServiceFunctionARN')
        # Kitchen Service Function
        self.kitchen_service_function = self.get_function_on_cross_stack(
                                                            'KitchenServiceFunctionARN')
        self.create_ticket_saga_function = self.kitchen_service_function
        self.confirm_create_ticket_saga_function = self.kitchen_service_function
        self.cancel_create_ticket_saga_function = self.kitchen_service_function
        # Account Service Function
        self.authorize_card_saga_function = self.get_function_on_cross_stack(
                                                            'AccountServiceFunctionARN')

        # -----------------------------------------------------
        # tasks
        # -----------------------------------------------------
        # Todo: task生成の順版に注意する。
        #  task catchで後続のtaskを利用するため。
        #  このようにしてるのは一つのLambda functionで複数のtaskを実現してるため
        # Order service Tasks
        self.approve_order_task = self.task_approve_order()
        self.reject_order_task = self.task_reject_order()
        # Consumer service Tasks
        self.validate_consumer_task = self.task_validate_consumer()
        # Kitchen service Tasks
        self.create_ticket_task = self.task_create_ticket()
        self.cancel_create_ticket_task = self.task_cancel_create_ticket()
        self.confirm_create_ticket_task = self.task_confirm_create_ticket()
        # Account service Tasks
        self.authorize_card_task = self.task_authorize_card()

        # State Machine
        self.state_machine = self.create_state_machine()

    def get_function_on_cross_stack(self, export_name):
        lambda_function_arn = aws_cdk.Fn.import_value(export_name)  # from CfnOutput()
        function = aws_cdk.aws_lambda.Function.from_function_arn(
            self, f'From{export_name}', lambda_function_arn)
        return function

    # -------------------------------------------------------
    # State Machine
    # -------------------------------------------------------
    def create_state_machine(self):
        state_machine = aws_stepfunctions.StateMachine(
            self,
            'CreateOrderSagaStateMachine',
            state_machine_name='CreateOrderSaga',
            definition=self.create_order_definition(),
            timeout=Duration.minutes(3),
            tracing_enabled=True)
        return state_machine

    # -------------------------------------------------------
    # task definition
    # -------------------------------------------------------
    def create_order_definition(self):
        definition = \
            self.validate_consumer_task\
                .next(self.create_ticket_task)\
                .next(self.authorize_card_task)\
                .next(self.confirm_create_ticket_task)\
                .next(self.approve_order_task)
        return definition

    # 補償トランザクション definition
    def reject_order_compensation_transaction_definition(self):
        # approve_consumerが失敗したときの補償トランザクション
        definition = self.reject_order_task
        return definition

    # 補償トランザクション definition
    def cancel_create_ticket_compensation_transaction_definition(self):
        # authorize_card が失敗したときの補償トランザクション
        definition = self.cancel_create_ticket_task\
            .next(self.reject_order_task)
        return definition

    # -------------------------------------------------------
    # tasks
    # -------------------------------------------------------
    def task_validate_consumer(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "CreateOrderSaga",
            "action": "VALIDATE_CONSUMER"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_details.$": "$.order_details",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskValidateConsumer',
            lambda_function=self.validate_consumer_saga_function,
            payload=payload,
            result_path='$.validate_consumer_result',
            output_path='$')

        task.add_catch(self.reject_order_compensation_transaction_definition(),
                       errors=['ConsumerVerificationFailedException',
                               'ConsumerNotFoundException'],
                       result_path='$.validate_consumer_result')  # 注意: $にするとinputが上書きされる。
        return task

    def task_reject_order(self):
        # ------------------------ payload ----------------------------
        payload = aws_stepfunctions.TaskInput.from_object({
                "task_context": aws_stepfunctions.TaskInput.from_object({
                                            "state_machine": "CreateOrderSaga",
                                            "action": "REJECT_ORDER"}),
                'order_id': aws_stepfunctions.JsonPath.string_at('$.order_id'),
                # Todo: ↓↓↓　必要ないかも
                'validate_consumer_result': aws_stepfunctions.JsonPath.string_at(
                                                                    '$.validate_consumer_result'),
                # Todo: inputをすべてほしい時に使う　
                #   'input': aws_stepfunctions.TaskInput.from_json_path_at('$'),
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskRejectOrder',
            lambda_function=self.reject_order_function,
            payload=payload,
            result_path='$.reject_order_result',  # Todo: 注意　$にするとinputが上書きされる。
            output_path='$')

        return task

    def task_approve_order(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "CreateOrderSaga",
            "action": "APPROVE_ORDER"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
                "order_id.$": "$.order_id",
                "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
            })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskApproveOrder',
            lambda_function=self.approve_order_function,
            # Todo: Taskコンテキストを追加する
            # payload=aws_stepfunctions.TaskInput.from_json_path_at('$'),
            payload=payload,
            result_path='$.approve_order_result',  # Todo: ここがポイント　$にするとinputが上書きされる。
            output_path='$')

        return task

    def task_create_ticket(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "CreateOrderSaga",
            "action": "CREATE_TICKET"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "restaurant_id.$": "$.order_details.restaurant_id",
            "order_line_items.$": "$.order_details.order_line_items",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # Todo: (注)パスを使用して値が選択されるキーと値のペアの場合、キー名は .$ で終わる必要があります。
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskCreateTicket',
            lambda_function=self.create_ticket_saga_function,
            payload=payload,
            result_path='$.create_ticket_result',  # 注意: $にするとinputが上書きされる。
            output_path='$')
        return task

    def task_authorize_card(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "CreateOrderSaga",
            "action": "AUTHORIZE_CARD"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "consumer_id.$": "$.order_details.consumer_id",
            "order_total.$": "$.order_details.order_total",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # Todo: (注)パスを使用して値が選択されるキーと値のペアの場合、キー名は .$ で終わる必要があります。
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskAuthorizeCard',
            lambda_function=self.authorize_card_saga_function,
            payload=payload,
            result_path='$.authorize_card_result',  # 注意: $にするとinputが上書きされる。
            output_path='$')

        task.add_catch(self.cancel_create_ticket_compensation_transaction_definition(),
                       errors=['CardAuthorizationFailedException',
                               'AccountNotFoundException'],
                       result_path='$.authorize_card_result')  # 注意: $にするとinputが上書きされる。
        return task

    def task_cancel_create_ticket(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "CreateOrderSaga",
            "action": "CANCEL_CREATE_TICKET"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "ticket_id.$": "$.create_ticket_result.Payload.ticket_id",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # Todo: (注)パスを使用して値が選択されるキーと値のペアの場合、キー名は .$ で終わる必要があります。
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskCancelCreateTicket',
            # lambda_function=self.create_ticket_saga_function,
            lambda_function=self.cancel_create_ticket_saga_function,
            payload=payload,
            result_path='$.cancel_create_ticket_result',  # 注意: $にするとinputが上書きされる。
            output_path='$')

        return task

    def task_confirm_create_ticket(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "CreateOrderSaga",
            "action": "CONFIRM_CREATE_TICKET"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "ticket_id.$": "$.create_ticket_result.Payload.ticket_id",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # Todo: (注)パスを使用して値が選択されるキーと値のペアの場合、キー名は .$ で終わる必要があります。
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskConfirmCreateTicket',
            lambda_function=self.confirm_create_ticket_saga_function,
            payload=payload,
            result_path='$.confirm_create_ticket_result',  # 注意: $にするとinputが上書きされる。
            output_path='$')

        return task
