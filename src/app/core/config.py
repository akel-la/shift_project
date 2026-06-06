from pathlib import Path

from pydantic import SecretStr
from pydantic import computed_field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Возможно, временная мера, пока не доработаю Dockerfile и docker-compose.yaml:
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../src/app/core/config.py
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # В названиях переменных используем POSTGRES, так как именно такие
    # названия переменных POSTGRES ищет по умолчанию:
    POSTGRES_USER: str | None = None
    # SecretStr + get_secret_value - для работы с паролями и прочими
    # подобными данными, чтобы они в логи не попадали:
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None

    @computed_field  # Для pydantic, чтобы он считал это частью окружения.
    @property
    def DATABASE_URL(self) -> str:  # noqa
        if self.POSTGRES_HOST:
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            return "sqlite+aiosqlite:///./shift_data.db"

    model_config = SettingsConfigDict(
        # Игнорировать переменные окружения, которых нет в этом классе:
        extra="ignore",
        env_file=ENV_FILE,
        env_file_encoding="utf_8",
    )


settings = Settings()
# Временная отладка:
print(settings.model_dump())
