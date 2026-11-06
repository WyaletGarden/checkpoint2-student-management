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
   uv sync --locked
   ```

2. Tạo hoặc chỉnh file `.env` theo cơ sở dữ liệu muốn dùng. Ví dụ chạy cục bộ với SQLite:

   ```dotenv
   DATABASE_URL=sqlite:///./students.db
   JWT_SECRET_KEY=
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
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

Mở giao diện tại http://127.0.0.1:8001 hoặc tài liệu API tại http://127.0.0.1:8001/docs. Frontend được phục vụ cùng backend, không cần chạy riêng.
`APP_PORT` trong `.env` chỉ điều khiển cổng host của Docker Compose; khi chạy Python trực tiếp, dùng tùy chọn `--port` như trên.

## Chạy bằng Docker

Yêu cầu Docker Desktop đang chạy Linux containers và Docker Compose. Không cần Python/uv/Node.js trên host cho cách chạy này.
Tạo `.env` từ mẫu nếu chưa có, giữ nguyên file hiện tại nếu đã cấu hình:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Điền `POSTGRES_PASSWORD` (chuỗi URL-safe) và `JWT_SECRET_KEY` (ít nhất 32 byte UTF-8) trong `.env`.
Nếu cần tạo mới, dùng lệnh sau rồi chép hai giá trị vào file; giữ nguyên các khóa đã dùng với database hiện có:

```powershell
docker run --rm python:3.12-slim python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_hex(32)); print('JWT_SECRET_KEY=' + secrets.token_hex(48))"
```

Khởi động cả app, PostgreSQL và Redis:

```powershell
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

Với `APP_PORT=8002` mặc định trong `.env.example`, mở http://127.0.0.1:8002/ hoặc http://127.0.0.1:8002/docs.
Compose đợi PostgreSQL/Redis healthy, chạy migration, rồi mở API và frontend. PostgreSQL và Redis không publish cổng ra host.
Các kết nối trong container dùng `db:5432` và `redis:6379`; Compose ghi đè cấu hình database/Redis dùng cho chạy Python trên host.
Xem [DOCKER.md](DOCKER.md) để kiểm tra cache, xử lý xung đột cổng, chạy SQLite độc lập và quản lý volume.
Nếu trước đây dùng `.env.compose`, chuyển nguyên mật khẩu PostgreSQL sang `.env`; cấu hình riêng vẫn được hỗ trợ bằng `--env-file .env.compose`.

Kiểm tra tích hợp và dừng dịch vụ:

```powershell
Get-Content -Raw -Encoding UTF8 scripts/compose_smoke.py | docker compose exec -T app python -
docker compose down
```

`down` giữ dữ liệu PostgreSQL trong volume. Thêm `--volumes` sẽ xóa database. Không commit `.env` hoặc thông tin đăng nhập riêng.

## Sử dụng

- Đăng ký tài khoản trên giao diện, sau đó đăng nhập.
- Tài khoản mới có quyền `user`, chỉ được xem dữ liệu. Quyền `admin` mới được thêm, sửa, xóa.
- Để cấp quyền admin đầu tiên, xem hướng dẫn trong [AUTH.md](AUTH.md).
- Khi nhập dữ liệu mới, nên tạo giảng viên → lớp học → sinh viên.
- API chính: `/register`, `/login`, `/api/v1/students/`, `/api/v1/classes/`, `/api/v1/teachers/`.
- Khi gọi API quản lý, gửi header `Authorization: Bearer <access_token>`. Trong Swagger, dùng nút **Authorize** để nhập token.

## Các API có sẵn

- `POST /register`: đăng ký, tài khoản mới có quyền `user`.
- `POST /login`: nhận JWT access token.
- `GET /api/v1/students/`, `GET /api/v1/students/{student_id}`: danh sách và chi tiết sinh viên.
- `POST /api/v1/students/`, `PUT /api/v1/students/{student_id}`, `DELETE /api/v1/students/{student_id}`: quản lý sinh viên.
- `GET /api/v1/classes/`, `GET /api/v1/classes/{id}`: danh sách và chi tiết lớp.
- `POST /api/v1/classes/`, `PUT /api/v1/classes/{id}`, `DELETE /api/v1/classes/{id}`: quản lý lớp.
- `GET /api/v1/teachers/`, `GET /api/v1/teachers/{id}`: danh sách và chi tiết giảng viên.
- `POST /api/v1/teachers/`, `PUT /api/v1/teachers/{id}`, `DELETE /api/v1/teachers/{id}`: quản lý giảng viên.
- `GET /demo/fixed-n-plus-1`: minh họa tải quan hệ sinh viên/lớp, yêu cầu admin.

Các API quản lý yêu cầu JWT; thao tác POST/PUT/DELETE yêu cầu admin. Đọc danh sách/chi tiết dùng được với cả user và admin.
Danh sách hỗ trợ `skip`, `limit` (1–100), `q` (tối đa 100 ký tự). Sinh viên có thêm `class_id` và `sort_by` (`score_asc`, `score_desc`, `first_name`, `last_name`).
Danh sách trả tổng số bản ghi phù hợp bộ lọc qua header `X-Total-Count`. Xem schema request/response đầy đủ tại `/docs` hoặc `/openapi.json`.

Ví dụ đăng ký, đăng nhập và đọc API bằng PowerShell (chọn username chưa tồn tại; nếu đã có tài khoản thì bỏ qua đăng ký):

```powershell
$api = 'http://127.0.0.1:8002'
$credentials = @{ username = 'student01'; password = 'StrongPassword123!' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$api/register" -ContentType 'application/json' -Body $credentials
$login = Invoke-RestMethod -Method Post -Uri "$api/login" -ContentType 'application/json' -Body $credentials
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri "$api/api/v1/students/?skip=0&limit=10" -Headers $headers
```

## Cấu trúc

- `app/api/`: các endpoint REST API.
- `app/services/`, `app/crud/`: xử lý nghiệp vụ và truy vấn dữ liệu.
- `app/models/`, `app/schemas/`: mô hình dữ liệu và kiểm tra đầu vào/đầu ra.
- `app/core/`: cấu hình, kết nối database và bảo mật.
- `frontend/`: giao diện web.
- `alembic/`: quản lý thay đổi cấu trúc database.
- `tests/`: kiểm thử.

## Cache danh sách sinh viên

`GET /api/v1/students/` sử dụng Redis để lưu kết quả danh sách và tổng số bản ghi (`X-Total-Count`).
Mỗi bộ tham số `class_id`, `sort_by`, `skip`, `limit`, `q` có cache riêng; các request vẫn phải xác thực JWT.

Cấu hình trong `.env`:

```dotenv
REDIS_HOST=localhost
REDIS_PORT=6379
STUDENTS_CACHE_TTL_SECONDS=60
STUDENTS_CACHE_NAMESPACE=student-management
```

Compose đã có Redis nội bộ. Khi chạy Python trực tiếp trên máy, có thể dùng Redis riêng trên cổng 6380 và đặt `REDIS_PORT=6380` trong `.env`:

```powershell
docker run --rm -d --name student-cache -p 127.0.0.1:6380:6379 redis:8-alpine
```

Đặt `STUDENTS_CACHE_TTL_SECONDS=0` để tắt cache. Khi chạy ứng dụng trong container, đặt `REDIS_HOST` theo hostname Redis mà container truy cập được.
Nếu nhiều môi trường hoặc database độc lập dùng chung Redis, đặt `STUDENTS_CACHE_NAMESPACE` khác nhau cho từng môi trường để tách dữ liệu cache.
Cache được làm mới sau khi thêm/sửa/xóa sinh viên, sửa lớp, hoặc sửa/xóa giảng viên vì response chứa cả thông tin lớp và cố vấn.
Các request đang đọc dữ liệu cũ không thể ghi lại vào phiên cache mới sau những thay đổi này.

Redis bị lỗi hoặc cache không hợp lệ thì API đọc database. Lỗi ghi/xóa cache không làm thao tác database thất bại; nếu không làm mới cache được khi Redis lỗi, dữ liệu cũ có thể còn được trả về đến khi TTL hết.
Thay đổi trực tiếp database bên ngoài API cũng chỉ được phản ánh sau khi cache hết hạn.

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
Workflow cũng chạy khi mở/cập nhật pull request và có thể chạy thủ công bằng `workflow_dispatch`.
Ba job chạy độc lập: backend dùng Python 3.12 và dependency trong `uv.lock` để chạy pytest; frontend dùng Node.js 24 để chạy test JavaScript;
Docker Compose integration build/chạy ba service, kiểm tra API/cache thực và xác nhận volume PostgreSQL giữ dữ liệu sau khi tạo lại container.

Unit test dùng SQLite và Redis giả; job Compose dùng PostgreSQL/Redis thật trong project kiểm thử riêng, với khóa test và cleanup tự động. Không cần cấu hình GitHub Secrets.
Sau khi commit và push workflow, mở tab **Actions → Test suite** trên GitHub để xem kết quả và log từng job. Test thất bại sẽ khiến job tương ứng báo lỗi.
