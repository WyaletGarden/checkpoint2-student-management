# Đóng gói và triển khai Student Management bằng Docker

**1. Mục tiêu và mô hình triển khai**

Project Student Management sử dụng FastAPI để cung cấp REST API và phục vụ giao diện web. Docker được sử dụng để đóng gói mã nguồn, Python và các thư viện thành image, giúp ứng dụng chạy trong môi trường nhất quán mà không cần cài trực tiếp Python hoặc PostgreSQL trên máy triển khai.

Quy trình gồm: chuẩn bị project → viết Dockerfile → build image ứng dụng → chuẩn bị cấu hình runtime → dùng Docker Compose tạo và chạy container → kiểm tra hoạt động.

Trong mô hình này, service `app` chạy FastAPI/Uvicorn; service `db` chạy PostgreSQL 17. Hai service giao tiếp qua network do Compose quản lý. Dữ liệu PostgreSQL được lưu trong named volume để giữ lại khi container được tạo lại.

Image là gói dùng để tạo container; container là môi trường được tạo từ image để chạy ứng dụng. Vì vậy, thao tác chính xác là **build image**, sau đó **tạo và chạy container**. Image sau khi build xuất hiện tại mục Images trong Docker Desktop. Quy trình dưới đây sử dụng image trên máy local và không yêu cầu đẩy image lên Docker Hub.

**2. Chuẩn bị môi trường**

Cài Docker Desktop, cấu hình WSL 2 và sử dụng Linux containers. Mở Docker Desktop, đợi engine sẵn sàng, sau đó mở PowerShell tại thư mục project:

```powershell
Set-Location 'D:\Checkpoint2_WebFramework_REST-API\Student_Management'
docker version
docker compose version
```

`docker version` cần hiển thị cả Client và Server. Nếu terminal trên máy hiện tại chưa nhận lệnh Docker dù đã cài Docker Desktop theo tài khoản Windows, có thể bổ sung PATH cho phiên PowerShell hiện tại:

```powershell
$env:Path += ";$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
docker version
docker compose version
```

Project cần có `requirements.txt`, thư mục `app`, `frontend`, `alembic` và file `alembic.ini`. Dependency được cài trong quá trình build image nên không cần kích hoạt môi trường ảo trên Windows.

**3. Viết Dockerfile**

Tạo file tên `Dockerfile`, không có phần mở rộng, tại thư mục gốc project. Nội dung sử dụng đúng cấu hình hiện tại:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/students.db

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY frontend/ ./frontend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data /app/logs \
    && chown appuser:appuser /data /app/logs

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`FROM` chọn image Python 3.12 bản slim làm nền tảng. `ENV` tắt việc tạo bytecode và cho phép xuất log ngay. `WORKDIR /app` đặt thư mục làm việc, phù hợp với đường dẫn tương đối `frontend` của ứng dụng.

File `requirements.txt` được copy và cài trước mã nguồn để Docker có thể tái sử dụng layer dependency khi chỉ thay đổi source. Các lệnh `COPY` tiếp theo đưa backend, frontend và migration vào image. `--no-cache-dir` tránh lưu cache pip trong image.

User `appuser` được tạo với UID/GID 10001 và được cấp quyền ghi vào `/data`, `/app/logs`. Lệnh `USER` giúp ứng dụng chạy bằng tài khoản thường. `EXPOSE 8000` mô tả cổng ứng dụng; ánh xạ cổng ra Windows được cấu hình ở Compose.

`CMD` khởi động Uvicorn tại `0.0.0.0:8000`. Dockerfile có URL SQLite mặc định để hỗ trợ cách chạy độc lập; trong quy trình Compose bên dưới, biến `DATABASE_URL` được ghi đè bằng URL PostgreSQL. Xem [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) để đối chiếu các chỉ thị.

**4. Tạo file .dockerignore**

File `.dockerignore` nằm cùng cấp với Dockerfile. Project hiện đã có file này; các nhóm loại trừ chính gồm:

```text
.git
.venv
venv
.uv_cache
.pytest_cache
.mypy_cache
.ruff_cache
.vscode
.idea
.agents
.codex
.aws
.env
.env.*
**/__pycache__
**/*.py[cod]
**/*.db
**/*.db-*
**/*.sqlite
**/*.sqlite-*
**/*.sqlite3
**/*.sqlite3-*
**/*.log
logs
tests
node_modules
build
dist
.coverage
htmlcov
```

Các quy tắc này loại môi trường ảo, cache, database, log và file chứa cấu hình bí mật khỏi build context. Thư viện cần thiết được cài mới trong image từ `requirements.txt`. Không cần copy môi trường ảo Windows vào container Linux.

**5. Viết docker-compose.yml**

Tạo file `docker-compose.yml` tại thư mục gốc. Nội dung tương ứng với cấu hình đang dùng:

```yaml
name: student-management

services:
  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: student_management
      POSTGRES_USER: student
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env.compose}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U \"$${POSTGRES_USER}\" -d \"$${POSTGRES_DB}\""]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: student-management:compose
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg://student:${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env.compose}@db:5432/student_management
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?Set JWT_SECRET_KEY in .env.compose}
      SQL_ECHO: "${SQL_ECHO:-false}"
      ACCESS_TOKEN_EXPIRE_MINUTES: "${ACCESS_TOKEN_EXPIRE_MINUTES:-30}"
      CORS_ORIGINS: "${CORS_ORIGINS:-[]}"
    ports:
      - "127.0.0.1:${APP_PORT:-8000}:8000"
    depends_on:
      db:
        condition: service_healthy
        restart: true
    command:
      - /bin/sh
      - -c
      - >-
        python -m alembic upgrade head &&
        exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=3).close()"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s

volumes:
  postgres-data:
```

Service `db` sử dụng image PostgreSQL có sẵn; service `app` sử dụng image được build từ project. `context: .` chọn thư mục hiện tại làm build context. `image: student-management:compose` quy định tên và tag cho image ứng dụng.

Trong network Compose, app kết nối PostgreSQL bằng hostname `db` và cổng `5432`. Không sử dụng `localhost` trong URL này vì `localhost` bên trong container app trỏ về chính container app. PostgreSQL không cần publish cổng ra Windows.

`depends_on` với `service_healthy` yêu cầu database vượt qua healthcheck trước khi app khởi động. Sau đó app chạy `alembic upgrade head` để cập nhật schema; chỉ khi migration thành công, Uvicorn mới được chạy. Migration được thực hiện lúc chạy container vì cần kết nối đến database runtime. Xem [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).

Named volume `postgres-data` được gắn vào thư mục dữ liệu của PostgreSQL 17. Với tên project hiện tại, volume mặc định có tên `student-management_postgres-data`.

**6. Build project thành image**

Chạy lệnh sau tại thư mục gốc:

```powershell
docker build -t student-management:compose .
if ($LASTEXITCODE -ne 0) { throw 'Build image that bai. Kiem tra log truoc khi tiep tuc.' }
docker image ls student-management
```

`-t student-management:compose` đặt tên image là `student-management`, tag là `compose`. Dấu `.` chỉ build context là thư mục hiện tại. Docker đọc Dockerfile, tải base image nếu cần, cài dependency và đóng gói mã nguồn thành image.

Kết quả mong đợi: danh sách image có `student-management` với tag `compose`. Có thể mở Docker Desktop → Images để chụp ảnh minh chứng. Đây là image local; bước build chưa tạo container ứng dụng chạy lâu dài.

Lệnh tương đương trong quy trình Compose là `docker compose --env-file .env.compose build app`, sử dụng sau khi đã chuẩn bị file môi trường. Trong trình tự này dùng `docker build` trước để có image phục vụ việc tạo khóa ở bước tiếp theo. Không cần chạy cả hai cách build.

**7. Chuẩn bị cấu hình môi trường**

Tạo `.env.compose` từ mẫu nếu chưa có:

```powershell
if (-not (Test-Path -LiteralPath '.env.compose')) {
    Copy-Item -LiteralPath '.env.compose.example' -Destination '.env.compose'
}
```

Với file mới, dùng image vừa build để tạo hai chuỗi hex ngẫu nhiên, không cần Python trên Windows:

```powershell
docker run --rm student-management:compose python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_hex(32)); print('JWT_SECRET_KEY=' + secrets.token_hex(48))"
notepad .env.compose
```

Copy hai giá trị vừa tạo vào các dòng tương ứng trong `.env.compose`. Container tạm dùng để tạo khóa sẽ tự xóa sau khi chạy. Lệnh này thay thế CMD mặc định nên không khởi động API và không cần cấu hình JWT trước đó.

File môi trường sau khi điền có dạng sau; các phần trong dấu `<...>` phải được thay bằng giá trị thật, không copy nguyên các chuỗi mô tả:

```dotenv
POSTGRES_PASSWORD=<chuoi_hex_ngau_nhien_64_ky_tu>
JWT_SECRET_KEY=<chuoi_hex_ngau_nhien_96_ky_tu>
APP_PORT=8000
SQL_ECHO=false
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=[]
```

Khóa JWT phải có ít nhất 32 byte UTF-8. Mật khẩu hex phù hợp vì Compose ghép mật khẩu vào URL kết nối database. `CORS_ORIGINS=[]` phù hợp với giao diện được phục vụ cùng origin bởi API.

Nếu file `.env.compose` đã được cấu hình và database đã có dữ liệu, giữ nguyên mật khẩu và khóa JWT đang dùng. Thay `POSTGRES_PASSWORD` trong file không tự đổi mật khẩu của database đã khởi tạo. Không đưa giá trị secret thật vào nội dung hoặc ảnh chụp báo cáo.

Nếu cổng 8000 đang được sử dụng, chọn `APP_PORT=8001`. Compose chỉ đọc file này khi lệnh có `--env-file .env.compose`; tên file không làm nó được tự động nạp. Biến môi trường trùng tên trong phiên PowerShell có độ ưu tiên cao hơn file, vì vậy cần kiểm tra nếu cấu hình hiệu lực khác dự kiến. Xem [Compose environment interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/).

**8. Kiểm tra cấu hình và tải image PostgreSQL**

Sau khi lưu file môi trường, chạy:

```powershell
docker compose --env-file .env.compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Cau hinh Compose chua hop le. Dung tai day de kiem tra.' }

docker compose --env-file .env.compose pull db
if ($LASTEXITCODE -ne 0) { throw 'Chua tai duoc image PostgreSQL.' }

docker image ls postgres
```

`config --quiet` xác thực cấu hình mà không in cấu hình đã thay biến ra terminal. Cần xử lý lỗi cấu hình trước khi tiếp tục. `pull db` tải image `postgres:17`, không build PostgreSQL từ mã nguồn project.

**9. Tạo và chạy các container**

Sau khi image ứng dụng đã build và image PostgreSQL đã tải thành công:

```powershell
docker compose --env-file .env.compose up --no-build --pull never -d --wait
if ($LASTEXITCODE -ne 0) { throw 'Stack chua khoi dong thanh cong. Kiem tra ps va logs.' }
```

`--no-build` sử dụng image đã build ở bước 6. `--pull never` sử dụng các image đã có trên máy. `-d` chạy nền. `--wait` chờ service đạt trạng thái chạy/healthy theo cấu hình healthcheck. Xem [docker compose up](https://docs.docker.com/reference/cli/docker/compose/up/).

Compose tạo network, volume nếu chưa có, sau đó khởi động PostgreSQL. Khi database sẵn sàng, app chạy migration và khởi động Uvicorn. Với project hiện tại và không có override khác, tên container mặc định là `student-management-db-1` và `student-management-app-1`.

Mở Docker Desktop → Containers để quan sát nhóm `student-management` và hai service. Ở giai đoạn này, image và container xuất hiện ở hai mục tương ứng trong Docker Desktop.

**10. Kiểm tra trạng thái, giao diện và database**

Chạy lần lượt:

```powershell
docker compose --env-file .env.compose ps -a
docker compose --env-file .env.compose logs --tail 50 app db
docker compose --env-file .env.compose images
```

Kết quả mong đợi: cả `app` và `db` đang chạy và có trạng thái healthy. Log app thể hiện Alembic đã xử lý migration và Uvicorn khởi động thành công. Nếu khởi động thất bại ở bước trước, vẫn dùng các lệnh `ps -a` và `logs` để xác định nguyên nhân.

Các lệnh sau lấy địa chỉ cổng đã publish từ Compose nên dùng được cho cả `APP_PORT=8000` và `APP_PORT=8001`:

```powershell
$appAddress = docker compose --env-file .env.compose port app 8000
if ($LASTEXITCODE -ne 0 -or -not $appAddress) { throw 'Khong lay duoc dia chi app.' }
$appBaseUrl = "http://$($appAddress.Trim())"

(Invoke-WebRequest -UseBasicParsing "$appBaseUrl/").StatusCode
(Invoke-WebRequest -UseBasicParsing "$appBaseUrl/docs").StatusCode
(Invoke-WebRequest -UseBasicParsing "$appBaseUrl/openapi.json").StatusCode
```

Kết quả mong đợi của ba lệnh HTTP là `200`. Với `APP_PORT=8000`, truy cập giao diện tại `http://127.0.0.1:8000/` và Swagger tại `http://127.0.0.1:8000/docs`. Với port 8001, thay cổng tương ứng.

Để kiểm tra kết nối database từ chính container app:

```powershell
docker compose --env-file .env.compose exec app python -c "from sqlalchemy import text; from app.core.database import engine; c=engine.connect(); print(c.execute(text('SELECT current_database(), current_user')).one()); c.close()"
docker compose --env-file .env.compose exec app python -m alembic current
docker compose --env-file .env.compose exec db psql -U student -d student_management -c '\dt'
```

Kết quả mong đợi: truy vấn trả database `student_management` và user `student`; Alembic ở revision head của source đang triển khai; danh sách bảng có `teachers`, `classes`, `students`, `users` và `alembic_version`. Với bộ migration hiện tại, revision head là `b82d4e5f6a70`.

Tiếp tục đăng ký, đăng nhập và gọi một API cần xác thực để kiểm tra luồng sử dụng thực tế. HTTP `200` ở `/openapi.json` chỉ xác nhận API phục vụ schema, chưa xác nhận database hoạt động; vì vậy bước truy vấn SQL ở trên cần được thực hiện riêng.

**11. Cập nhật mã nguồn, dừng và chạy lại**

Khi source hoặc dependency thay đổi, build lại và cập nhật container bằng:

```powershell
docker compose --env-file .env.compose up --build -d --wait
```

Compose build image ứng dụng và tạo lại container khi image hoặc cấu hình thay đổi. Các volume đang gắn được giữ lại. Theo [docker compose build](https://docs.docker.com/reference/cli/docker/compose/build/), image được gắn tên đã khai báo tại trường `image`.

Khi chỉ cần tạm dừng:

```powershell
docker compose --env-file .env.compose stop
```

Khi cần chạy lại các container đã có:

```powershell
docker compose --env-file .env.compose start --wait
```

Khi kết thúc phiên thực hành và muốn xóa container/network nhưng vẫn giữ dữ liệu:

```powershell
docker compose --env-file .env.compose down
```

Không thêm `-v` nếu cần giữ volume PostgreSQL. Sau `down`, sử dụng lại lệnh `up` ở bước 9 để tạo container từ các image đã có và gắn lại dữ liệu cũ. Không sử dụng `start` sau `down` vì container đã bị xóa.

**12. Nội dung ghi nhận và ảnh minh chứng**

Báo cáo nên kèm ảnh Dockerfile, cấu hình Compose, kết quả build image, mục Images trong Docker Desktop, trạng thái hai service healthy, giao diện web/Swagger và kết quả truy vấn SQL từ container app. Che giá trị secret nếu chúng xuất hiện trong ảnh.

Sau khi thực hiện, có thể ghi nhận kết quả theo mẫu: “Project được đóng gói thành image `student-management:compose`. Docker Compose tạo hai container ứng dụng và PostgreSQL. Ứng dụng kết nối database qua hostname `db`, migration được thực hiện trước khi khởi động API, giao diện và tài liệu API được truy cập qua cổng đã cấu hình. Dữ liệu PostgreSQL được quản lý bằng named volume.” Chỉ sử dụng các nhận định này sau khi đã đối chiếu với kết quả thực tế.

Cấu hình hiện tại phù hợp cho thực hành local với một app container. Khi triển khai lâu dài, các hướng cải thiện gồm tách tài khoản PostgreSQL của app khỏi tài khoản superuser, bổ sung readiness kiểm tra database, quản lý log rotation và tách migration thành bước triển khai riêng khi chạy nhiều replica. Tài khoản khởi tạo qua `POSTGRES_USER` có quyền superuser theo [tài liệu PostgreSQL image](https://hub.docker.com/_/postgres).

Tài liệu này mô tả quy trình và kết quả mong đợi. Việc soạn tài liệu không đồng nghĩa các lệnh build, khởi động container hay kiểm thử đầu cuối đã được thực thi lại.
