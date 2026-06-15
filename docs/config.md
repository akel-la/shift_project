```python
class Settings(BaseSettings):
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    ...
    @computed_field
    def REFRESH_TOKEN_MINUTES(self) -> int:
        return self.REFRESH_TOKEN_DAYS * 24 * 60
```

1. SecretStr вместо str - чтобы данные не попадали в файл логов при ошибке, что может привести к утечке секретных данных.

2. Названия, начинающиеся с POSTGRES, обязательно должны называться именно так, так как именно такие переменные окружения ищет PostgreSQL.

3. Функция REFRESH_TOKEN_MINUTES - делаем ее вычисляемой, чтобы срок жизни refresh токенов задавать в удобном виде: в днях.
Время в минутах вычисляется, поэтому @computed_field, но при этом без @property, так как нам нужно вычислить только один раз, а не каждый раз при обращении к атрибуту.
