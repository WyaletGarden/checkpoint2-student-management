from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field, SecretStr, TypeAdapter, field_validator
from urllib.parse import urlsplit

class Settings(BaseSettings):
    PROJECT_NAME: str = "Student Management API"
    DATABASE_URL: str = "sqlite:///./students.db"
    JWT_SECRET_KEY: SecretStr
    SQL_ECHO: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    CORS_ORIGINS: list[str] = Field(default_factory=list)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if not secret.strip() or len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 UTF-8 bytes")
        return value

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                "*" in origin or origin != origin.strip()
                or parsed.scheme not in {"http", "https"}
                or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.path
                or "?" in origin or "#" in origin
            ):
                raise ValueError("CORS origins must be explicit HTTP(S) origins without credentials, paths, queries or fragments")
            TypeAdapter(AnyHttpUrl).validate_python(origin)
        return origins

    model_config = SettingsConfigDict(env_file=".env", hide_input_in_errors=True)

# Khởi tạo instance settings để các file khác có thể import vào dùng
settings = Settings()
