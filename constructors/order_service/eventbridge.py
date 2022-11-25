import aws_cdk
from constructs import Construct
from aws_cdk import Duration
from aws_cdk import aws_stepfunctions
from aws_cdk import aws_stepfunctions_tasks
from aws_cdk import aws_iam
from aws_cdk import aws_sqs
from aws_cdk import aws_sns
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_event_sources


class StepFunctionsCallbackPattern(Construct):

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self.queue, self.callback_lambda = self.sqs_queue_and_callback_lambda()
        step_function = self.state_machine()
        step_function.grant_task_response(self.callback_lambda)

        # Test用 StepFunction実行するテスト用Lambda Function
        self.lambda_function_for_test(step_function)

    def state_machine(self):
        state_machine = aws_stepfunctions.StateMachine(
            self,
            'SQSCallbackPattern',
            state_machine_name='SQSCallbackPattern',
            definition=self.definition(),
            timeout=Duration.minutes(3),
            tracing_enabled=True)
        return state_machine

    def definition(self):
        callback_pattern_definition = \
            self.tasks_sqs_send_message_with_callback()\
            .next(
                self.choice_callback_result()
                    .when(
                        aws_stepfunctions.Condition.string_equals('$.callback_result', 'SUCCESS'),
                        next=self.task_success_process_lambda())
                    .when(
                        aws_stepfunctions.Condition.string_equals('$.callback_result', 'ERROR'),
                        next=self.task_error_process_lambda())
                    .otherwise(
                        self.task_exception_process_lambda()
                    )
            )
        return callback_pattern_definition

    def tasks_sqs_send_message_with_callback(self):
        sqs_send_message = aws_stepfunctions_tasks.SqsSendMessage(
            self,
            'TaskSqsSendMessage',
            integration_pattern=aws_stepfunctions.ServiceIntegrationPattern.WAIT_FOR_TASK_TOKEN,
            queue=self.queue,
            message_body=aws_stepfunctions.TaskInput.from_object({
                'Input.$': '$',  # ここの$はPayloadの配下
                'TaskToken': aws_stepfunctions.JsonPath.task_token
            }),
            result_path='$.callback_result',
            output_path='$')
        return sqs_send_message

    def choice_callback_result(self):
        callback_choice = aws_stepfunctions.Choice(self, 'ChoiceCallbackResult')
        # callback_choice.when(
        #     aws_stepfunctions.Condition.string_equals('$.callback_result', 'SUCCESS'),
        #     self.task_success_process_lambda()
        # )
        #
        # callback_choice.when(
        #     aws_stepfunctions.Condition.string_equals('$.callback_result', 'ERROR'),
        #     self.task_error_process_lambda()
        # )
        return callback_choice

    def task_success_process_lambda(self):

        success_function = aws_lambda.Function(
            self,
            'SuccessProcessLambdaFunction',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('lambda/success')
        )

        success_lambda_task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskSuccessProcessLambda',
            lambda_function=success_function,
            payload=aws_stepfunctions.TaskInput.from_json_path_at('$'),  # $: default input
            result_path='$.lambda_result',
            output_path='$')
        return success_lambda_task

    def task_error_process_lambda(self):

        error_function = aws_lambda.Function(
            self,
            'ErrorProcessLambdaFunction',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('lambda/error')
        )

        error_lambda = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskErrorProcessLambda',
            lambda_function=error_function,
            payload=aws_stepfunctions.TaskInput.from_json_path_at('$'),  # $: default input
            result_path='$.lambda_result',  # Todo: ここがポイント
            output_path='$')
        return error_lambda

    def task_exception_process_lambda(self):

        exception_function = aws_lambda.Function(
            self,
            'ExceptionProcessLambdaFunction',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('lambda/exception')
        )

        exception_lambda = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            'TaskExceptionProcessLambda',
            lambda_function=exception_function,
            payload=aws_stepfunctions.TaskInput.from_json_path_at('$'),  # $: default input
            result_path='$.lambda_result',  # Todo: ここがポイント
            output_path='$')
        return exception_lambda

    def sqs_queue_and_callback_lambda(self):
        queue = aws_sqs.Queue(
            self,
            'StepFunctionCallbackPatternSqsQueue',
            visibility_timeout=Duration.seconds(300))

        callback_function = aws_lambda.Function(
            self,
            'SqsInvokeCallbackFunction',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('lambda/sqs_invoke_callback_function')
        )

        # SQS invoke Lambda Function
        event_source = aws_lambda_event_sources.SqsEventSource(queue)
        callback_function.add_event_source(event_source)

        return queue, callback_function

    def lambda_function_for_test(self, stepfunction):
        test_function = aws_lambda.Function(
            self,
            'StartStepfunctionForTest',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('lambda/test_function'),
            environment={
                'STATE_MACHINE_ARN': stepfunction.state_machine_arn
            }
        )
