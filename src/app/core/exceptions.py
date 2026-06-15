class ServiceError(Exception):
    """
    Суперкласс всех исключений уровня сервисов.
    """

    def __init__(self, message: str = "Внутренняя ошибка."):
        self.message = message
        super().__init__(message)


class ConflictError(ServiceError):
    """
    Конфликт согласованности данных -
    невозможно корректно выполнить операцию
    с такими данными.
    """

    def __init__(self, message: str = "Невозможно выполнить запрос с такими данными."):
        super().__init__(message)


class NotFoundError(ServiceError):
    """
    Сущность не найдена.
    """

    def __init__(self, message: str = "Запрашиваемая сущность не найдена."):
        super().__init__(message)


class UnauthorizedError(ServiceError):
    """
    Ошибка аутентификации.
    (Мы не знаем, что за пользователь).
    """

    def __init__(self, message: str = "Пользователь не авторизован."):
        super().__init__(message)


class ForbiddenError(ServiceError):
    """
    Доступ запрещён.
    (Мы знаем, что за пользователь,
    но он не имеет полномочий для данной операции).
    """

    def __init__(self, message: str = "Недостаточно прав для этого запроса."):
        super().__init__(message)
