class EventAnswerTimeoutError(TimeoutError):
    def __init__(self, message: str = "Error! Event timed out while waiting for answer!") -> None:
        super().__init__(message)
