from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import Base, engine

# Khởi tạo bảng CSDL
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# --- GLOBAL EXCEPTION HANDLER ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Bắt mọi lỗi không mong muốn (Unhandled Exceptions / 500 Internal Server Error)
    Ngăn chặn việc lộ Traceback ra bên ngoài và trả về JSON thống nhất.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "Đã xảy ra lỗi không mong muốn từ hệ thống. Vui lòng thử lại sau."
            # Lưu ý: Trong môi trường dev, bạn có thể thay detail bằng str(exc) để dễ debug.
        },
    )

# Gắn router API vào app
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Student Management API is running perfectly!"}