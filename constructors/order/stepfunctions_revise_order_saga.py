import aws_cdk
from constructs import Construct
from aws_cdk import Duration
from aws_cdk import aws_stepfunctions
from aws_cdk import aws_stepfunctions_tasks

"""
{
  "input": {
    "consumer_id": 4,
    "event_id": "10449101fc15472d81b51a0683f7efa5",
    "order_revision": {
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
      "revised_order_line_items": [
        {
          "quantity": 3,
          "menu_id": "000001"
        },
        {
          "quantity": 2,
          "menu_id": "000002"
        },
        {
          "quantity": 1,
          "menu_id": "000003"
        }
      ]
    },
    "order_id": "6320092bf02b4896849d432b5fd5a7ed",
    "channel": "ReviseOrderSagaRequested"
  },
}
"""


class ReviseOrderSagaStepFunctions(Construct):

    def __init__(self, scope: Construct, id: str, props: dict) -> None:
        super().__init__(scope, id)
        self.props = props

        # ------------------------------------------------------
        # Saga 参加 function
        # ------------------------------------------------------
        # Order Service Function
        self.begin_revise_order_function = props.get('order_service_function')
        self.confirm_revise_order_function = props.get('order_service_function')
        self.undo_begin_revise_order_function = props.get('order_service_function')

        # Kitchen Service Function
        self.kitchen_service_function = self.get_function_on_cross_stack(
                                                                'KitchenServiceFunctionARN')
        self.begin_revise_ticket_function = self.kitchen_service_function
        self.confirm_revise_ticket_function = self.kitchen_service_function
        self.undo_begin_revise_ticket_function = self.kitchen_service_function

        # Account Service Function
        self.revise_authorize_card_saga_function = self.get_function_on_cross_stack(
                                                                'AccountServiceFunctionARN')

        # -----------------------------------------------------
        # tasks
        # -----------------------------------------------------
        # Todo: task生成の順版に注意する。
        #  task catchで後続のtaskを利用するため。
        #  このようにしてるのは一つのLambda functionで複数のtaskを実現してるため
        # Order service Tasks
        self.begin_revise_order_task = self.task_begin_revise_order()
        self.confirm_revise_order_task = self.task_confirm_revise_order()
        self.undo_begin_revise_order_task = self.task_undo_begin_revise_order()

        # Kitchen service Tasks
        self.begin_revise_ticket_task = self.task_begin_revise_ticket()
        self.confirm_revise_ticket_task = self.task_confirm_revise_ticket()
        self.undo_begin_revise_ticket_task = self.task_undo_begin_revise_ticket()

        # Account service Tasks
        self.revise_authorize_card_task = self.task_revise_authorize_card()

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
            'ReviseOrderSagaStateMachine',
            state_machine_name='ReviseOrderSaga',
            definition=self.revise_order_definition(),
            timeout=Duration.minutes(3),
            tracing_enabled=True)
        return state_machine

    # -------------------------------------------------------
    # task definition
    # -------------------------------------------------------
    def revise_order_definition(self):
        definition = \
            self.begin_revise_order_task\
                .next(self.begin_revise_ticket_task)\
                .next(self.revise_authorize_card_task)\
                .next(self.confirm_revise_ticket_task)\
                .next(self.confirm_revise_order_task)
        return definition

    # 補償トランザクション definition
    def begin_revise_ticket_error_compensation_transaction_definition(self):
        # begin_revise_ticketが失敗したときの補償トランザクション
        definition = self.undo_begin_revise_order_task
        return definition

    # 補償トランザクション definition
    def revise_authorize_card_error_compensation_transaction_definition(self):
        # revise_authorizeが失敗したときの補償トランザクション
        definition = \
            self.undo_begin_revise_ticket_task\
                .next(self.undo_begin_revise_order_task)
        return definition

    # -------------------------------------------------------
    # tasks
    # -------------------------------------------------------
    def task_begin_revise_order(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "BEGIN_REVISE_ORDER"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "order_revision.$": "$.order_revision",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskBeginReviseOrder',
            lambda_function=self.begin_revise_order_function,
            payload=payload,
            result_path='$.begin_revise_order_result',
            output_path='$')

        # task.add_catch(self.reject_order_compensation_transaction_definition(),
        #                errors=['ConsumerVerificationFailedException',
        #                        'ConsumerNotFoundException'],
        #                result_path='$.validate_consumer_result')  # 注意: $にするとinputが上書きされる。
        return task

    def task_confirm_revise_order(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "CONFIRM_REVISE_ORDER"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "order_revision.$": "$.order_revision",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskConfirmReviseOrder',
            lambda_function=self.confirm_revise_order_function,
            payload=payload,
            result_path='$.confirm_revise_order_result',  # Todo: 注意　$にするとinputが上書きされる。
            output_path='$')

        return task

    def task_undo_begin_revise_order(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "UNDO_BEGIN_REVISE_ORDER"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskUndoBeginReviseOrder',
            lambda_function=self.undo_begin_revise_order_function,
            payload=payload,
            result_path='$.undo_begin_revise_order_result',
            output_path='$')

        return task

    def task_begin_revise_ticket(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "BEGIN_REVISE_TICKET"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "revised_order_line_items.$": "$.order_revision.revised_order_line_items",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskBeginReviseTicket',
            lambda_function=self.begin_revise_ticket_function,
            payload=payload,
            result_path='$.begin_revise_ticket_result',
            output_path='$')

        task.add_catch(self.begin_revise_ticket_error_compensation_transaction_definition(),
                       errors=['UnsupportedStateTransitionException',
                               'TicketNotFoundException'],
                       result_path='$.begin_revise_ticket_result')  # 注意: $にするとinputが上書きされる
        return task

    def task_revise_authorize_card(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "REVISE_AUTHORIZE_CARD"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "consumer_id.$": "$.consumer_id",
            "order_id.$": "$.order_id",
            "new_order_total.$": "$.begin_revise_order_result.Payload.new_order_total",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskReviseAuthorizeCard',
            lambda_function=self.revise_authorize_card_saga_function,
            payload=payload,
            result_path='$.revise_authorize_card_result',
            output_path='$')

        task.add_catch(self.revise_authorize_card_error_compensation_transaction_definition(),
                       errors=['CardAuthorizationFailedException',
                               'AccountNotFoundException'],
                       result_path='$.revise_authorize_card_result')

        return task

    def task_undo_begin_revise_ticket(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "UNDO_BEGIN_REVISE_TICKET"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskUndoBeginReviseTicket',
            lambda_function=self.undo_begin_revise_ticket_function,
            payload=payload,
            result_path='$.undo_begin_revise_ticket_result',
            output_path='$')

        return task

    def task_confirm_revise_ticket(self):
        # ------------------------ payload ----------------------------
        task_context = {
            "state_machine": "ReviseOrderSaga",
            "action": "CONFIRM_REVISE_TICKET"
        }
        payload = aws_stepfunctions.TaskInput.from_object({
            "order_id.$": "$.order_id",
            "revised_order_line_items.$": "$.order_revision.revised_order_line_items",
            "task_context": aws_stepfunctions.TaskInput.from_object(task_context)
        })
        # ------------------------ payload ----------------------------

        task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskConfirmReviseTicket',
            lambda_function=self.confirm_revise_ticket_function,
            payload=payload,
            result_path='$.confirm_revise_ticket_result',
            output_path='$')

        # task.add_catch(self.reject_order_compensation_transaction_definition(),
        #                errors=['ConsumerVerificationFailedException',
        #                        'ConsumerNotFoundException'],
        #                result_path='$.validate_consumer_result')  # 注意: $にするとinputが上書きされる。
        return task
