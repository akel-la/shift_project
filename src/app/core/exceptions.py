class ConflictError(Exception):
    def __init__(self, message: str = "Ошибка ..."):
        self.message = message
        super().__init__(message)


class NotFoundError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
