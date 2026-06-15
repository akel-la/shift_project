```python
def verify_password(password: str, hashed: str) -> bool:
    """Проверяет пароль"""
    try:
        ph.verify(hashed, password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False
```

Мы не возбуждаем исключение, а при любых проблемах просто возвращаем False, чтобы на уровне REST API всегда при проблемах возвращать 401 Unauthorized, так как мы не хотим раскрывать пользователям особенности работы очень важной части бекенда, которая связанна с безопасностью.
