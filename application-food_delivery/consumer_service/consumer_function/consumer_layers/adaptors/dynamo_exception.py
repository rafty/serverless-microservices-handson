import contextlib
from botocore import exceptions
from consumer_layers.common import exceptions

""" DynamoDB Exceptions """


class ConditionalCheckFailedException(Exception):
    pass


class ResourceNotFoundException(Exception):
    pass


class TransactionCanceledException(Exception):
    pass


class TransactionConflictException(Exception):
    pass


class ItemCollectionSizeLimitExceededException(Exception):
    pass


class ProvisionedThroughputExceededException(Exception):
    pass


@contextlib.contextmanager
def dynamo_exception_check():
    try:
        yield

    except exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(e.response['Error'])
            # raise ConditionalCheckFailedException(
            #     f'ConditionalCheckFailedException: {e.response["Error"]}')
            raise exceptions.ConsumerNameAlreadyExists(e.response['Error'])

        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ResourceNotFoundException(f'ResourceNotFoundException: {e.response["Error"]}')

        if e.response['Error']['Code'] == 'TransactionCanceledException':
            code_set = {reason.get('Code') for reason in e.response['CancellationReasons']}  # Set内包表記
            if 'ConditionalCheckFailed' in code_set:
                raise ConditionalCheckFailedException(
                    f'ConditionalCheckFailedException: {e.response["Error"]}')
            else:
                raise TransactionCanceledException(f'TransactionCanceledException: {e.response["Error"]}')

        if e.response['Error']['Code'] == 'TransactionConflictException':
            raise TransactionConflictException(
                f'TransactionConflictException: {e.response["Error"]}')

        if e.response['Error']['Code'] == 'ItemCollectionSizeLimitExceededException':
            raise ItemCollectionSizeLimitExceededException(
                f'ItemCollectionSizeLimitExceededException: {e.response["Error"]}')

        if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
            raise ProvisionedThroughputExceededException(
                f'ProvisionedThroughputExceededException: {e.response["Error"]}')
        else:
            raise Exception(f'DynamoDB Exception: {e.response["Error"]}')
    except Exception as e:
        raise Exception(f'DynamoDB Exception: {e}')
