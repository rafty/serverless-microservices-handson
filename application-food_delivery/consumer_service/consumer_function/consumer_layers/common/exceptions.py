class UnsupportedRoute(Exception):
    pass


class InvalidName(Exception):
    pass


class UnsupportedStateTransitionException(Exception):
    pass


class UnsupportedOperationException(Exception):
    pass


class ConsumerNotFoundException(Exception):
    pass


class ConsumerNameAlreadyExists(Exception):
    pass


class InvalidCurrency(Exception):
    pass


class ItemNotFoundException(Exception):
    pass


class InvalidSagaCmd(Exception):
    pass


# -------------------------------------------------
# For Create Order Saga Compensation Transaction 補償トランザクション
# -------------------------------------------------
class ConsumerVerificationFailedException(Exception):
    pass
