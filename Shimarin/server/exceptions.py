class EventAnswerTimeoutError(TimeoutError):
    def __init__(self, message: str = "Event timed out while waiting for answer") -> None:
        super().__init__(message)


class CallbackIsLambdaError(AssertionError):
    def __init__(self, message: str = "Callback cannot be lambda function") -> None:
        super().__init__(message)


class UnknownStatusError(AssertionError):
    def __init__(self, message: str = "Invalid event status, allowed values are 'delivered', 'done', 'failed', 'waiting'") -> None:
        super().__init__(message)