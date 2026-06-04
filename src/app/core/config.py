from pydantic import SecretStr
from pydantic import computed_field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    # В названиях переменных используем POSTGRES, так как именно такие
    # названия переменных POSTGRES ищет по умолчанию:
    POSTGRES_USER: str
    # SecretStr + get_secret_value - для работы с паролями и прочими
    # подобными данными, чтобы они в логи не попадали:
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    @computed_field  # Для pydantic, чтобы он считал это частью окружения.
    @property
    def DATABASE_URL(self) -> str:  # noqa
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        # Игнорировать переменные окружения, которых нет в этом классе:
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf_8",
    )


settings = Settings()
