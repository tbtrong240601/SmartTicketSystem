# SmartTicketSystem

Ứng dụng quản lý Ticket dùng Flask, SQLAlchemy và Flask-Migrate.

## Chạy local trên Windows (PowerShell)

Đã kiểm tra với Python 3.14.7. Cài thư viện trong môi trường riêng:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY = "replace-with-your-local-secret"
```

Chạy thử với SQLite, không cần cài MySQL:

```powershell
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///smart_ticket_dev.db"
.\.venv\Scripts\python.exe -m flask --app run db upgrade
.\.venv\Scripts\python.exe -m flask --app run run --debug
```

Database SQLite được tạo trong `instance/`. Mở http://127.0.0.1:5000 và đăng ký tài khoản User.
Ứng dụng chưa có chức năng quản trị để tạo tài khoản IT Support/Admin.

Nếu dùng MySQL, tạo database `smart_ticket_db` trước, rồi đặt URI phù hợp:

```powershell
$env:SQLALCHEMY_DATABASE_URI = "mysql+pymysql://USER:PASSWORD@localhost/smart_ticket_db"
```

Mật khẩu chứa ký tự đặc biệt phải được URL-encode trong URI.
Thứ tự cấu hình database: `SQLALCHEMY_DATABASE_URI` → `DATABASE_URL` →
`mysql+pymysql://root:@localhost/smart_ticket_db` (fallback local cũ).
`SECRET_KEY` có fallback chỉ dành cho development; đặt giá trị riêng khi triển khai.
Ứng dụng đọc biến môi trường của tiến trình; không tự nạp file `.env`.
Chỉ dùng `--debug` khi phát triển local.

## Nâng cấp database hiện có

Sao lưu database và thử nâng cấp bản sao trước khi chạy trên dữ liệu đang sử dụng.
Đặt URI trỏ đúng database, rồi kiểm tra revision:

```powershell
.\.venv\Scripts\python.exe -m flask --app run db current
.\.venv\Scripts\python.exe -m flask --app run db upgrade
.\.venv\Scripts\python.exe -m flask --app run db check
```

- Database trống: chạy toàn bộ chuỗi migration để tạo schema.
- Database đã ở revision `1e6b9640cdac`: chỉ chạy migration sửa timestamp mới.
- Database đã được quản lý bằng migration ở revision cũ hơn: Alembic tiếp tục từ revision đó.
  Nếu schema đã bị thay đổi thủ công hoặc bởi `create_all()`, cần đối chiếu schema trước;
  migration lịch sử có thể gặp cột trùng.
- Database đã có bảng nhưng không có revision: **không chạy upgrade hoặc stamp head một cách mù quáng**.
  Cần đối chiếu bảng, cột, kiểu dữ liệu, khóa ngoại và nullability với một revision cụ thể,
  sau đó mới stamp đúng revision đã xác minh rồi upgrade. Repo không tự stamp hay xóa dữ liệu.

Revision `000000000001` bổ sung phần tạo bảng mà migration đầu tiên trước đây giả định đã có.
Database đã có revision sẽ không chạy lại phần tạo bảng này. ID của các migration cũ được giữ nguyên;
migration đầu tiên được nối với baseline mới. Khóa ngoại mới có tên rõ ràng và default thời gian
dùng biểu thức SQLAlchemy để tương thích SQLite/MySQL.

Revision `000000000002` thêm `updated_at`, `resolved_at`, `closed_at` nếu chưa tồn tại.
Khi thêm `updated_at`, giá trị của Ticket cũ được lấy từ `created_at`;
không suy đoán thời điểm xử lý/đóng, nên hai cột đó để NULL cho dữ liệu cũ.
Các cột và giá trị timestamp đã tồn tại được giữ nguyên.
Migration sửa này cần kết nối database để kiểm tra schema, không hỗ trợ xuất SQL offline.
Nó chỉ hỗ trợ nâng cấp; để quay lại cần khôi phục bản sao lưu, tránh xóa cột có dữ liệu từ trước.

Ứng dụng không tự tạo hay nâng cấp bảng khi khởi động.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các test dùng database SQLite tạm riêng: dựng schema mới, nâng cấp dữ liệu cũ,
giữ timestamp có sẵn, chạy upgrade lặp lại và luồng tạo → tiếp nhận → xử lý → xác nhận → đóng Ticket.
Không kết nối database trong cấu hình local của bạn. MySQL thực tế cần được kiểm tra riêng.

## Các phần còn thiếu

- `it_ticket_detail.html` chưa tồn tại dù route chi tiết Ticket của IT/Admin đang gọi template này.
- `base_it.html` chưa tồn tại; dashboard tiếp tục dùng `base.html`.
- Admin, quản lý Category/User/Role, Knowledge Base và AI chưa được bổ sung trong đợt sửa cấu trúc.
