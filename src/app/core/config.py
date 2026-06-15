from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic import computed_field
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Чтобы Settings видел файл .env:
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # Режимы работы:
    ENVIRONMENT: Literal["dev", "prod"] = "dev"

    # Только для prod:
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None

    # JWT:
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int
    REFRESH_TOKEN_DAYS: int

    # Админ:
    CREATE_INITIAL_ADMIN: bool = True
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: SecretStr

    @computed_field
    def REFRESH_TOKEN_MINUTES(self) -> int:  # noqa
        return self.REFRESH_TOKEN_DAYS * 24 * 60

    @model_validator(mode="after")
    def validate_postgres_settings(self):
        """
        Если запуск с PostgreSQL - то все переменные
        должны быть заданы.
        """
        if self.ENVIRONMENT == "prod":
            missing = []
            if not self.POSTGRES_USER:
                missing.append("POSTGRES_USER")
            # Особая проверка, так как SecretStr:
            if self.POSTGRES_PASSWORD is None:
                missing.append("POSTGRES_PASSWORD")
            if not self.POSTGRES_DB:
                missing.append("POSTGRES_DB")
            if not self.POSTGRES_HOST:
                missing.append("POSTGRES_HOST")
            if not self.POSTGRES_PORT:
                missing.append("POSTGRES_PORT")

            if missing:
                raise ValueError(
                    f"Проект запущен в режиме ENVIRONMENT == 'prod'"
                    f"но отсутствуют переменные окружения:\n"
                    f"{','.join(missing)}"
                )
        return self

    # Порядок декораторов:
    # Сначала @property - метод становится свойством.
    # Потом @computed_field - регистрация свойства как вычисляемого свойства.
    @computed_field  # Для pydantic, чтобы он считал это частью окружения.
    @property
    def DATABASE_URL(self) -> str:  # noqa
        if self.ENVIRONMENT == "prod":
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            return f"sqlite+aiosqlite:///{BASE_DIR}/shift_data.db"

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=ENV_FILE,
        env_file_encoding="utf_8",
    )


settings = Settings()
