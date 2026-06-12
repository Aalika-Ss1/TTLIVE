class DomainError(ValueError):
    """Raised when a Tournament OS business rule is violated."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
