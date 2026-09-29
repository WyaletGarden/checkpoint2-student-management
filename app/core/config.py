from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Student Management API"
    DATABASE_URL: str = "sqlite:///./students.db"

    class Config:
        env_file = ".env"

# Khởi tạo instance settings để các file khác có thể import vào dùng
settings = Settings()