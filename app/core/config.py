from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Student Management API"
    DATABASE_URL: str = "sqlite:///./students.db"

    model_config = SettingsConfigDict(env_file=".env")

# Khởi tạo instance settings để các file khác có thể import vào dùng
settings = Settings()
