"""
Перехватывает исключения уровня бизнес логики
и сопоставляет их с HTTP ответами.
Для работы нужно подключить к app = FastAPI(...) в main.py.
"""

from fastapi import status
from fastapi.responses import JSONResponse

from .exceptions import ConflictError
from .exceptions import ForbiddenError
from .exceptions import NotFoundError
from .exceptions import ServiceError
from .exceptions import UnauthorizedError

excs_mapping = {
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
}


async def service_exception_handler(request, exc: ServiceError):
    response_code = excs_mapping.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(
        status_code=response_code,
        content={"detail": exc.message},
    )
