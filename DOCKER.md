# Chạy Student Management bằng Docker

Luồng mặc định dùng ba service: FastAPI (`app`), PostgreSQL 17 (`db`) và Redis 8 (`redis`).
Docker Compose tạo network riêng, chạy migration trước API và giữ dữ liệu PostgreSQL trong volume.
Không cần cài Python, uv hoặc Node.js trên máy host để chạy ứng dụng bằng Compose.

## 1. Chuẩn bị

Cài [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/), bật Linux containers và đợi engine sẵn sàng.
Chạy các lệnh PowerShell tại thư mục gốc dự án:

```powershell
docker version
docker compose version
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Nếu terminal chưa nhận Docker ở bản cài theo tài khoản Windows, mở lại terminal hoặc thêm PATH cho phiên hiện tại:

```powershell
$env:Path += ";$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
```

Điền `POSTGRES_PASSWORD` và `JWT_SECRET_KEY` trong `.env`. Có thể tạo hai giá trị bằng Docker:

```powershell
docker run --rm python:3.12-slim python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_hex(32)); print('JWT_SECRET_KEY=' + secrets.token_hex(48))"
```

Chép các giá trị vào file, không commit `.env`. Giữ nguyên JWT key và mật khẩu PostgreSQL qua các lần khởi động.
Mật khẩu PostgreSQL được ghép vào URL nên dùng ký tự URL-safe, ví dụ chuỗi hex được tạo ở trên.
Nếu chuyển từ cấu hình cũ `.env.compose`, giữ nguyên `POSTGRES_PASSWORD` của file đó khi đưa sang `.env`, vì volume PostgreSQL có thể đã tồn tại.

Các cấu hình chính:

```dotenv
POSTGRES_PASSWORD=
JWT_SECRET_KEY=
APP_PORT=8002
SQL_ECHO=false
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=[]
STUDENTS_CACHE_TTL_SECONDS=60
STUDENTS_CACHE_NAMESPACE=student-management
```

Hai trường mật khẩu/khóa phải được điền trước khi chạy. `APP_PORT` là cổng HTTP trên host.
Compose tự đặt URL database thành `db:5432` và địa chỉ Redis thành `redis:6379` trong container app;
các giá trị `DATABASE_URL`, `REDIS_HOST`, `REDIS_PORT` dùng cho chạy Python trên host không làm thay đổi kết nối nội bộ này.

## 2. Khởi động

```powershell
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

Với `APP_PORT=8002`, truy cập:

- Giao diện: http://127.0.0.1:8002/
- Swagger: http://127.0.0.1:8002/docs
- OpenAPI: http://127.0.0.1:8002/openapi.json

Cả ba service cần ở trạng thái healthy. App đợi database và Redis healthy trước khi chạy migration.
Nếu migration lỗi, Uvicorn không khởi động. App phục vụ cả frontend nên không cần container frontend riêng.
Chỉ app publish cổng ra host; PostgreSQL và Redis dùng network nội bộ, tránh xung đột các cổng 5432/6379 đang có trên máy.

```powershell
docker compose logs --tail 100 app db redis
```

Nếu vẫn muốn dùng file cấu hình riêng, các lệnh tương đương là
`docker compose --env-file .env.compose up --build -d --wait`.
`.env.compose.example` được giữ để hỗ trợ cách chạy tùy chọn này; luồng mặc định dùng `.env`.

## 3. Kiểm tra API, database và cache

Đăng ký/đăng nhập tại giao diện hoặc Swagger. Tài khoản mới có quyền user, đọc được danh sách.
Quyền admin để thêm/sửa/xóa được mô tả trong [AUTH.md](AUTH.md).

Chạy kiểm tra tích hợp tự động:

```powershell
Get-Content -Raw -Encoding UTF8 scripts/compose_smoke.py | docker compose exec -T app python -
```

Script kiểm tra frontend, Swagger, kết nối PostgreSQL, đăng ký/đăng nhập và API sinh viên;
đồng thời kiểm tra cache hit và TTL thực trên Redis. Nó dùng tài khoản và query ngẫu nhiên riêng,
sau đó xóa tài khoản/cache thử nghiệm. Cần để `STUDENTS_CACHE_TTL_SECONDS` lớn hơn 0.
Kết quả thành công kết thúc bằng `Compose smoke passed`.

Để quan sát cache thủ công:

```powershell
docker compose exec redis redis-cli MONITOR
```

Gọi cùng `GET /api/v1/students/` hai lần trong TTL: lần đầu có `SET ... EX 60`,
lần sau chỉ đọc cache. Khi tạo/sửa/xóa sinh viên, sửa lớp hoặc sửa/xóa giảng viên,
generation đổi; key cũ tự hết hạn. Nhấn Ctrl+C để dừng MONITOR.

Kết nối PostgreSQL để kiểm tra bảng:

```powershell
docker compose exec db psql -U student -d student_management
```

Trong psql: `\dt` xem các bảng, `\q` để thoát.

## 4. Dừng, cập nhật và giữ dữ liệu

```powershell
docker compose stop
docker compose start --wait
```

Sau khi sửa code hoặc migration:

```powershell
docker compose up --build -d --wait
```

Để tạo lại container và kiểm tra dữ liệu vẫn còn:

```powershell
docker compose up -d --force-recreate --wait
```

`docker compose down` xóa container/network và giữ volume PostgreSQL.
Chỉ dùng `docker compose down --volumes` khi muốn xóa cả database.
Redis chỉ giữ cache, không có volume; mất cache sẽ khiến request kế tiếp truy vấn database và tạo lại cache.

## 5. Chạy image độc lập với SQLite

Đây là cách chạy tùy chọn, không khởi động PostgreSQL/Redis. Ví dụ tắt cache và dùng cổng 8003:

```powershell
docker build -t student-management:local .
docker volume create student-management-data
docker run --rm --env-file .env -e DATABASE_URL=sqlite:////data/students.db --mount type=volume,source=student-management-data,target=/data student-management:local python -m alembic upgrade head
docker run -d --name student-management-sqlite --env-file .env -e DATABASE_URL=sqlite:////data/students.db -e STUDENTS_CACHE_TTL_SECONDS=0 --mount type=volume,source=student-management-data,target=/data -p 127.0.0.1:8003:8000 student-management:local
```

Mở http://127.0.0.1:8003/docs. Đây là database SQLite riêng trong volume, không tự sao chép dữ liệu trên host.

## 6. Cách image và CI được kiểm tra

Dockerfile dùng Python 3.12 slim, cài dependency từ `requirements.txt`, sau đó copy backend,
frontend và Alembic. App chạy bằng user thường; `/data` và `/app/logs` có quyền ghi.
`.dockerignore` loại secrets, database, log và môi trường phát triển khỏi image.

Job `Docker Compose integration` trên GitHub Actions dùng project, cấu hình và database kiểm thử riêng.
Job build/chạy ba service, thực hiện smoke test, tạo một bản ghi kiểm tra volume,
tạo lại container và xác nhận bản ghi còn tồn tại. Khi kết thúc, tài nguyên của project CI được dọn bằng `down --volumes`.

## 7. Xử lý lỗi thường gặp

- Không nhận lệnh Docker: kiểm tra cài đặt/PATH và mở lại terminal.
- Không kết nối engine: mở Docker Desktop, đợi engine sẵn sàng.
- Thiếu secret: điền `POSTGRES_PASSWORD` và `JWT_SECRET_KEY` trong `.env`.
- Cổng HTTP đang dùng: đổi `APP_PORT` sang cổng trống rồi chạy lại `up`; cổng trong app vẫn là 8000.
- Sai mật khẩu PostgreSQL với volume cũ: dùng mật khẩu lúc volume được khởi tạo; sửa biến môi trường không tự đổi mật khẩu trong database.
- Redis lỗi sau khi ứng dụng đã khởi động: API đọc database; cache cũ có thể tồn tại đến khi TTL hết nếu invalidation không thực hiện được.

Tham khảo: [Compose networking](https://docs.docker.com/compose/how-tos/networking/),
[startup order](https://docs.docker.com/compose/how-tos/startup-order/),
[PostgreSQL image](https://hub.docker.com/_/postgres).
