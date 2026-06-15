from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Literal

import jwt  # Это PyJWT, не python-jose.
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError
from argon2.exceptions import VerifyMismatchError

from .config import settings

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Хешируем пароль с помощью Argon2.
    """
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверяет пароль.
    """
    try:
        ph.verify(hashed, password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_token(
    data: dict,
    token_type: Literal["access", "refresh"],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()

    if token_type == "access":
        min = settings.ACCESS_TOKEN_MINUTES
    else:
        min = settings.REFRESH_TOKEN_MINUTES

    delta = expires_delta or timedelta(minutes=min)
    time = datetime.now(UTC)

    expire = time + delta
    # type - это что бы не возможно было выдать refresh
    # токен за access и наоборот - это дыра в безопасности:
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(
        to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError("Invalid token") from e
