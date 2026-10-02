from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import Base, engine

# Khởi tạo bảng CSDL
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        },
    )

# Gắn router API vào app
app.include_router(api_router, prefix="/api/v1")

# Gắn thư mục frontend vào đường dẫn gốc để phục vụ giao diện web trực tiếp
# html=True giúp trả về trang index.html khi truy cập http://127.0.0.1:8000/
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")