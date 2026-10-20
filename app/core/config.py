from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Student Management API"
    DATABASE_URL: str = "sqlite:///./students.db"
    JWT_SECRET_KEY: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(48)))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(env_file=".env")

# Khởi tạo instance settings để các file khác có thể import vào dùng
settings = Settings()
