# Viết Dockerfile, build và chạy thử

Chạy các lệnh PowerShell dưới đây tại thư mục gốc project, nơi chứa `Dockerfile`.
Ví dụ này dùng SQLite riêng cho container; database được lưu trong volume `student-management-data`.

Để chạy app và PostgreSQL bằng một lệnh, xem [Docker Compose](#docker-compose-app--postgresql).

## 1. Chuẩn bị Docker và cấu hình

Cài [Docker Desktop cho Windows](https://docs.docker.com/desktop/setup/install/windows-install/),
bật WSL 2 theo hướng dẫn cài đặt và dùng chế độ **Linux containers**.
Mở Docker Desktop, đợi engine sẵn sàng, rồi mở lại terminal trong IDE:

```powershell
docker version
```

Kết quả cần có cả phần `Client` và `Server`. Lỗi không nhận lệnh `docker` thường do chưa
cài Docker hoặc terminal chưa cập nhật PATH; lỗi kết nối engine thì kiểm tra Docker Desktop.

Trên máy hiện tại, Docker đã được tìm thấy ở bản cài theo tài khoản Windows.
Nếu terminal vẫn không nhận lệnh, thêm thư mục CLI vào PATH của **phiên PowerShell hiện tại**:

```powershell
$env:Path += ";$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
docker version
```

Nếu chưa có `.env`, tạo từ mẫu (giữ nguyên file đang dùng nếu đã có):

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Điền `JWT_SECRET_KEY` trong `.env` bằng chuỗi ngẫu nhiên có ít nhất 32 byte UTF-8.
Nếu cần tạo khóa mới sau khi build image ở bước 3:

```powershell
docker run --rm student-management:local python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Chép kết quả vào `JWT_SECRET_KEY=...`, giữ nguyên khóa khi khởi động lại. Không cần
Python hoặc uv trên máy host để build/chạy container. File `.env` không được đưa vào image;
`--env-file .env` sẽ truyền cấu hình vào container lúc chạy.

## 2. Hiểu Dockerfile của project

- `FROM python:3.12-slim`: bắt đầu từ image Python 3.12 bản gọn, phù hợp `requires-python` của project.
- `ENV`: tắt file bytecode, xuất log ngay và đặt SQLite mặc định tại `/data/students.db`.
- `WORKDIR /app`: các lệnh tiếp theo chạy trong `/app`, đúng với đường dẫn tương đối `frontend` của ứng dụng.
- `COPY requirements.txt` rồi `RUN ... pip install`: cài các phiên bản đã chốt trong project. Tách khỏi source để tận dụng cache khi chỉ sửa code.
- Các lệnh `COPY` còn lại đưa backend, frontend và Alembic vào image.
- `RUN groupadd ...` và `USER appuser`: chạy app bằng user thường; `/data` và `/app/logs` được cấp quyền ghi cho user này.
- `EXPOSE 8000`: mô tả cổng ứng dụng; cần `-p` ở bước chạy để truy cập từ máy host.
- `CMD [...]`: chạy Uvicorn tại `0.0.0.0:8000` để nhận kết nối qua cổng Docker. Không dùng `--reload` trong ví dụ này.

`.dockerignore` loại `.env`, môi trường ảo, database, log và cache khỏi build context.
Alembic chạy ở bước riêng sau khi có database và cấu hình runtime, không chạy khi build image.

## 3. Build image

```powershell
docker build -t student-management:local .
```

`-t` đặt tên và tag cho image; dấu `.` chọn thư mục hiện tại làm build context.
Lần đầu cần tải base image và các thư viện. Nếu bước cài thư viện lỗi, xem tên package
và phiên bản trong log; Dockerfile sử dụng nguyên `requirements.txt` của project.

## 4. Tạo bảng bằng container tạm

Đảm bảo đã điền `JWT_SECRET_KEY` trước khi chạy:

```powershell
docker volume create student-management-data
docker run --rm --env-file .env -e DATABASE_URL=sqlite:////data/students.db --mount type=volume,source=student-management-data,target=/data student-management:local python -m alembic upgrade head
```

Chỉ tiếp tục nếu migration kết thúc thành công. `--rm` xóa container migration sau khi
hoàn tất; volume vẫn giữ database. Phần `python -m alembic ...` thay thế `CMD` của image.
`-e DATABASE_URL=...` ghi đè URL trong `.env` để migration và API cùng dùng file trên volume.
Đây là database mới, không tự sao chép dữ liệu SQLite đang có trên máy host.

## 5. Chạy ứng dụng và kiểm tra

```powershell
docker run -d --name student-management --env-file .env -e DATABASE_URL=sqlite:////data/students.db --mount type=volume,source=student-management-data,target=/data -p 127.0.0.1:8000:8000 student-management:local
docker ps
docker logs --tail 50 student-management
```

`-d` chạy nền; `--name` đặt tên container; `-p 127.0.0.1:8000:8000` ánh xạ cổng
8000 trên máy của bạn vào cổng 8000 của container, chỉ cho truy cập từ máy này.

Đợi log xuất hiện `Application startup complete`, rồi mở:

- Giao diện: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs

Kiểm tra HTTP và thử đăng ký/đăng nhập trên giao diện để xác nhận database hoạt động:

```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/).StatusCode
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/openapi.json).StatusCode
```

Hai lệnh HTTP dự kiến trả `200`; chúng kiểm tra frontend và API schema, chưa kiểm tra truy vấn database.
Frontend được phục vụ trong cùng container nên không cần chạy server frontend riêng.

## 6. Dừng và chạy lại

```powershell
docker stop student-management
docker start student-management
```

Sau khi sửa source, build lại image ở bước 3, chạy migration nếu có thay đổi schema,
rồi tạo lại container để dùng image mới:

```powershell
docker stop student-management
docker rm student-management
```

Sau đó chạy lại lệnh `docker run -d ...` ở bước 5. Giữ nguyên volume và JWT key để
giữ dữ liệu và hiệu lực token. Log file nằm trong container; `docker logs` dùng để xem
log khi chạy thử, log cũ của container sẽ mất khi xóa container.

## Lỗi thường gặp

- Container thoát ngay: chạy `docker ps -a` và `docker logs student-management`; kiểm tra `JWT_SECRET_KEY` đủ dài và `CORS_ORIGINS` là mảng JSON hợp lệ.
- `no such table`: chạy migration ở bước 4, dùng đúng URL và volume như container API.
- Cổng 8000 đang bận: đổi thành `-p 127.0.0.1:8001:8000`, truy cập cổng `8001` trên trình duyệt.
- Tên container đã tồn tại: dùng `docker start student-management` để chạy lại container cũ hoặc dừng/xóa nó trước khi tạo container mới.
- Nếu chuyển sang PostgreSQL trên máy Windows: dùng hostname `host.docker.internal` thay cho `localhost` trong URL; cấu hình PostgreSQL cho phép kết nối phù hợp. Bỏ phần ghi đè SQLite và volume `/data` ở **cả** lệnh migration và API để dùng cùng URL PostgreSQL trong `.env`.

Tham khảo: [Dockerfile](https://docs.docker.com/reference/dockerfile/),
[docker run](https://docs.docker.com/reference/cli/docker/container/run/),
[Docker volumes](https://docs.docker.com/engine/storage/volumes/).

## Kết quả chạy thử ngày 30/10/2026

- Build thành công image `student-management:local` trên Docker Desktop, Linux containers.
- `alembic upgrade head` chạy thành công cả ba migration trên volume mới.
- Container `student-management` phục vụ tại http://127.0.0.1:8000/.
- `/`, `/docs`, `/openapi.json` đều trả HTTP `200` từ máy host.
- Đăng ký trả `201`, đăng nhập trả `200` và cấp JWT; đọc `/api/v1/students/` trả `200`.
- Tài khoản dùng để kiểm tra đã được xóa khỏi database.
- Tiến trình chạy với UID `10001`, ghi được `/data` và `/app/logs`; image không chứa `/app/.env`.

Đây là kiểm tra tích hợp nhanh trong container, chưa chạy toàn bộ bộ kiểm thử của project.

## Docker Compose: app + PostgreSQL

`docker-compose.yml` chạy hai service:

- `db`: PostgreSQL 17, lưu dữ liệu trong volume `student-management_postgres-data`.
- `app`: build từ Dockerfile hiện có, kết nối `db:5432`, chạy `alembic upgrade head`, rồi khởi động Uvicorn.

Compose tạo network chung và phân giải tên service `db` thành địa chỉ container PostgreSQL.
Trong container app, `localhost` là chính app, vì vậy URL phải dùng `db`, không dùng `localhost`.
Database không cần publish cổng ra Windows để app kết nối được.
Healthcheck `pg_isready` cùng `depends_on: condition: service_healthy` đảm bảo database
sẵn sàng trước khi app chạy migration. Migration lỗi thì Uvicorn không khởi động.
Ví dụ này dành cho một container app chạy cục bộ.

### Chuẩn bị cấu hình riêng

Giữ `.env` hiện tại để dùng cho cách chạy cũ. Compose dùng `.env.compose` và chỉ truyền
các biến cần thiết vào app; không tự dùng URL SQLite hoặc Aiven trong `.env`.
File `.env.compose` đã được bỏ qua bởi Git và Docker build context.

Nếu chưa có `.env.compose`, đoạn PowerShell sau tạo file với hai khóa ngẫu nhiên;
không ghi đè file đã có. `APP_PORT=8001` cho phép chạy song song với container SQLite cũ:

```powershell
if (-not (Test-Path .env.compose)) {
    $composeRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $composeDbBytes = New-Object byte[] 32
        $composeJwtBytes = New-Object byte[] 48
        $composeRng.GetBytes($composeDbBytes)
        $composeRng.GetBytes($composeJwtBytes)
        $composeDbPassword = [BitConverter]::ToString($composeDbBytes).Replace('-', '').ToLowerInvariant()
        $composeJwtKey = [BitConverter]::ToString($composeJwtBytes).Replace('-', '').ToLowerInvariant()
        $composeConfig = @(
            "POSTGRES_PASSWORD=$composeDbPassword"
            "JWT_SECRET_KEY=$composeJwtKey"
            'APP_PORT=8001'
            'SQL_ECHO=false'
            'ACCESS_TOKEN_EXPIRE_MINUTES=30'
            'CORS_ORIGINS=[]'
        )
        [System.IO.File]::WriteAllLines((Join-Path (Get-Location) '.env.compose'), $composeConfig, [System.Text.UTF8Encoding]::new($false))
    } finally {
        $composeRng.Dispose()
    }
}
```

Hoặc copy `.env.compose.example` thành `.env.compose`, tự điền hai khóa và chọn `APP_PORT`.
Mật khẩu PostgreSQL được ghép vào URL nên dùng ký tự URL-safe như khóa hex ở trên;
tránh các ký tự `@`, `:`, `/`, `#`, `%`, `$`. Khóa JWT cần ít nhất 32 byte UTF-8.
Không đổi `POSTGRES_PASSWORD` sau khi database đã khởi tạo: biến này chỉ đặt mật khẩu
trong lần khởi tạo volume trống; đổi mật khẩu DB hiện có cần thực hiện bằng SQL.

### Khởi động, kiểm tra và cập nhật code

Tại thư mục gốc project:

```powershell
docker compose --env-file .env.compose config --quiet
docker compose --env-file .env.compose up --build -d --wait
docker compose --env-file .env.compose ps
docker compose --env-file .env.compose logs --tail 50 app db
```

Với `APP_PORT=8001`, mở http://127.0.0.1:8001/ hoặc http://127.0.0.1:8001/docs.
Nếu chọn `APP_PORT=8000`, dùng cổng 8000 và dừng container cũ đang chiếm cổng đó.
Hai container xuất hiện trong nhóm `student-management` trên Docker Desktop.
Khi sửa code, chạy lại `up --build -d --wait`; Compose tự tạo lại app khi image thay đổi
và gắn lại volume PostgreSQL, không cần tự điền form Run.

Kiểm tra kết nối SQL từ chính container app, không in mật khẩu:

```powershell
docker compose --env-file .env.compose exec app python -c "from sqlalchemy import text; from app.core.database import engine; c=engine.connect(); print(c.execute(text('SELECT current_database(), current_user, version()')).one()); c.close()"
```

Mở terminal PostgreSQL để xem bảng:

```powershell
docker compose --env-file .env.compose exec db psql -U student -d student_management
```

Trong `psql`, dùng `\dt` để xem danh sách bảng, `SELECT id, username, role FROM users;`
để xem tài khoản và `\q` để thoát.

### Dừng và giữ dữ liệu

```powershell
docker compose --env-file .env.compose stop
docker compose --env-file .env.compose start --wait
```

Hoặc xóa các container cùng network nhưng giữ volume:

```powershell
docker compose --env-file .env.compose down
```

Sau đó chạy lại `up --build -d --wait` để tạo lại container và dùng database cũ.
Không thêm `-v` vào `down` nếu cần giữ dữ liệu PostgreSQL.
Đây là database mới, độc lập với SQLite và Aiven; tài khoản/dữ liệu cũ không tự chuyển sang.

### Kết quả chạy thử Compose ngày 30/10/2026

- `config --quiet` hợp lệ; `up --build -d --wait` thành công, cả `app` và `db` đều healthy.
- Kết nối SQL từ container app xác nhận PostgreSQL, hostname `db`, cổng `5432`, database `student_management` và database user `student`.
- Cả ba migration đã áp dụng, revision hiện tại là `b82d4e5f6a70`.
- Truy cập `/`, `/docs`, `/openapi.json` qua cổng 8001 đều trả HTTP `200`.
- Đăng ký trả `201`, đăng nhập và đọc danh sách sinh viên trả `200`; tài khoản mới được kiểm tra trực tiếp trong PostgreSQL.
- Tạo lại cả hai container bằng `up -d --force-recreate --wait` vẫn giữ dữ liệu trong volume `student-management_postgres-data`.
- Tài khoản và bảng tạm phục vụ kiểm tra đã được xóa sau khi xác nhận.

Tham khảo: [Compose networking](https://docs.docker.com/compose/how-tos/networking/),
[startup order](https://docs.docker.com/compose/how-tos/startup-order/),
[PostgreSQL image](https://hub.docker.com/_/postgres).
