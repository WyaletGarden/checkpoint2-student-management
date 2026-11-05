# Student Management

## CORS

API đọc danh sách origin được phép từ `CORS_ORIGINS` trong `.env` (mảng JSON). Xem `.env.example` để tạo cấu hình. Mặc định là `[]`: không cấp quyền CORS cho website khác origin; frontend được phục vụ cùng API vẫn hoạt động.

Frontend development chạy riêng:

```dotenv
CORS_ORIGINS=["http://localhost:5173"]
```

Production: thay domain ví dụ bằng domain frontend thực tế:

```dotenv
CORS_ORIGINS=["https://students.example.com","https://admin.example.com"]
```

Origin phải gồm `http://` hoặc `https://`, hostname và port nếu cần; không có dấu `/` cuối, đường dẫn, query, fragment hoặc thông tin đăng nhập. Không cho phép `*`, kể cả wildcard subdomain; cấu hình không hợp lệ khiến ứng dụng không khởi động. Scheme và port khác nhau là origin khác nhau. Khởi động lại API sau khi thay đổi cấu hình.

CORS cho phép `GET`, `POST`, `PUT`, `DELETE`, header `Authorization`, `Content-Type` và cho frontend đọc `X-Total-Count`. Middleware tự xử lý preflight `OPTIONS`. API dùng JWT Bearer, không bật cookie cross-origin (`allow_credentials=False`).

CORS là cơ chế của trình duyệt, không chặn `curl`, Postman hoặc server khác gọi API và không thay thế JWT, phân quyền.

Ứng dụng web quản lý sinh viên, lớp học và giảng viên. Backend dùng **FastAPI, SQLAlchemy, Alembic**; giao diện dùng **HTML, CSS, JavaScript**.

## Chức năng

- Xem, thêm, sửa, xóa sinh viên, lớp học và giảng viên.
- Tìm kiếm, phân trang; lọc sinh viên theo lớp và sắp xếp theo tên hoặc điểm.
- Đăng ký, đăng nhập bằng JWT; phân quyền `user` và `admin`.
- Hỗ trợ SQLite và PostgreSQL.

## Cách chạy

Yêu cầu: **Python 3.12 trở lên** và **uv**. Chạy các lệnh tại thư mục gốc dự án.

1. Cài thư viện:

   ```powershell
   uv sync
   ```

2. Tạo hoặc chỉnh file `.env` theo cơ sở dữ liệu muốn dùng. Ví dụ chạy cục bộ với SQLite:

   ```dotenv
   DATABASE_URL=sqlite:///./students.db
   JWT_SECRET_KEY=thay_bang_chuoi_bi_mat_ngau_nhien
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   SQL_ECHO=false
   ```

   Tạo khóa bí mật rồi chép kết quả vào `JWT_SECRET_KEY`:

   ```powershell
   uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   `JWT_SECRET_KEY` bắt buộc, không được để trống và phải có ít nhất 32 byte UTF-8. Dùng cùng một khóa cho mọi worker và giữ nguyên qua các lần khởi động; đổi khóa sẽ làm token cũ mất hiệu lực. Không commit khóa thật.

   `SQL_ECHO` mặc định là `false`. Chỉ bật `true` khi cần debug SQL rồi khởi động lại ứng dụng. Tham số truy vấn được ẩn trong log SQLAlchemy kể cả khi bật debug.

3. Tạo/cập nhật các bảng và khởi động:

   ```powershell
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload
   ```

Mở giao diện tại http://127.0.0.1:8000 hoặc tài liệu API tại http://127.0.0.1:8000/docs. Frontend được phục vụ cùng backend, không cần chạy riêng.

## Chạy bằng Docker

Xem [hướng dẫn viết Dockerfile, build và chạy thử container](DOCKER.md).
Ví dụ dùng SQLite trong Docker volume, chạy Alembic trước khi khởi động API và phục vụ cả frontend.

Để chạy app cùng PostgreSQL trong hai container, xem [Docker Compose](DOCKER.md#docker-compose-app--postgresql).
File `docker-compose.yml` tự đợi database sẵn sàng và chạy migration trước khi mở API.

## Sử dụng

- Đăng ký tài khoản trên giao diện, sau đó đăng nhập.
- Tài khoản mới có quyền `user`, chỉ được xem dữ liệu. Quyền `admin` mới được thêm, sửa, xóa.
- Để cấp quyền admin đầu tiên, xem hướng dẫn trong [AUTH.md](AUTH.md).
- Khi nhập dữ liệu mới, nên tạo giảng viên → lớp học → sinh viên.
- API chính: `/register`, `/login`, `/api/v1/students/`, `/api/v1/classes/`, `/api/v1/teachers/`.
- Khi gọi API quản lý, gửi header `Authorization: Bearer <access_token>`. Trong Swagger, dùng nút **Authorize** để nhập token.

## Cấu trúc

- `app/api/`: các endpoint REST API.
- `app/services/`, `app/crud/`: xử lý nghiệp vụ và truy vấn dữ liệu.
- `app/models/`, `app/schemas/`: mô hình dữ liệu và kiểm tra đầu vào/đầu ra.
- `app/core/`: cấu hình, kết nối database và bảo mật.
- `frontend/`: giao diện web.
- `alembic/`: quản lý thay đổi cấu trúc database.
- `tests/`: kiểm thử.

## Kiểm thử

```powershell
uv run pytest
```

Kiểm thử logic frontend (cần Node.js):

```powershell
node tests/frontend_auth.test.mjs
```

## GitHub Actions

Workflow [Test suite](.github/workflows/tests.yml) tự động chạy mỗi khi push lên bất kỳ branch nào, kể cả branch có tên chứa `/`.
Hai job chạy độc lập: backend dùng Python 3.12 và `uv sync --locked --dev` để cài đúng dependency trong `uv.lock`, sau đó chạy toàn bộ pytest; frontend dùng Node.js 24 để chạy test JavaScript.

CI dùng SQLite tạm và JWT key kiểm thử do `tests/conftest.py` thiết lập, không cần cấu hình GitHub Secrets hay khởi động Docker/PostgreSQL.
Sau khi commit và push workflow, mở tab **Actions → Test suite** trên GitHub để xem kết quả và log từng job. Test thất bại sẽ khiến job tương ứng báo lỗi.
