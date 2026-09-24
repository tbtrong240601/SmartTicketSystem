# SmartTicket System

Ứng dụng quản lý hỗ trợ IT bằng Flask, MariaDB/MySQL (hoặc SQLite), kèm Knowledge Base và tích hợp Groq.

## Chức năng

- **User:** đăng ký/đăng nhập, đổi mật khẩu, tạo/theo dõi Ticket, bình luận, xác nhận đã khắc phục hoặc trả lại xử lý.
- **IT Support:** tiếp nhận, chuyển phiếu, nhập phương án xử lý, chờ xác nhận rồi đóng Ticket; viết bài nháp Knowledge Base.
- **Admin:** dashboard, thống kê 7 ngày, khối lượng nhân viên, xuất CSV, quản lý danh mục, tạo tài khoản/đổi vai trò/khóa tài khoản/đặt lại mật khẩu; duyệt bài viết; xem nhật ký.
- **Knowledge Base:** tìm kiếm, lọc danh mục, bản nháp/xuất bản, tạo bản nháp từ phương án Ticket; chỉ bài đã xuất bản được dùng cho trợ lý.
- **AI:** truy xuất 3 bài liên quan bằng từ khóa tiếng Việt bỏ dấu; gọi Groq khi có khóa và người dùng cho phép gửi câu hỏi. Không có khóa hoặc dịch vụ lỗi thì hiển thị tra cứu nội bộ có nhãn rõ ràng.

## Chạy nhanh trên máy Windows hiện tại

1. Bật **MySQL** trong XAMPP. Database thực tế `smart_ticket_db` đã được nâng cấp đến revision `000000000003`.
2. Mở `start.bat` trong thư mục dự án. Lần đầu cần Python và Internet để cài dependencies.
3. Truy cập **http://127.0.0.1:5000**. Dừng bằng Ctrl+C trong cửa sổ máy chủ.
4. Tài khoản hiện có được giữ nguyên. Tài khoản Admin mới được bàn giao trong file riêng `TAI_KHOAN_ADMIN_LOCAL.txt`, không nằm trong ZIP hoặc Git. Đổi mật khẩu sau khi đăng nhập.

`start.bat` dùng Waitress, không bật debug, chỉ lắng nghe localhost. `serve.py` kiểm tra revision trước khi chạy và không tự sửa database. Nếu chưa có `.env`, lần khởi động đầu tự tạo SECRET_KEY ngẫu nhiên cho local.

## Cài từ đầu hoặc trên máy khác

Python đã kiểm tra: **3.14.7**. MariaDB đã kiểm tra: **10.4.32 (XAMPP)**.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
```

Đặt SECRET_KEY ngẫu nhiên và URI database trong `.env`. Tạo database MySQL trống trước nếu dùng MySQL. Hoặc dùng SQLite:

```powershell
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///smart_ticket_dev.db"
.\.venv\Scripts\python.exe -m flask --app run db upgrade
.\.venv\Scripts\python.exe -m flask --app run create-admin --username admin
.\.venv\Scripts\python.exe -m flask --app run seed-knowledge --author admin
.\.venv\Scripts\python.exe serve.py
```

Lệnh `create-admin` hỏi mật khẩu, không có tài khoản/mật khẩu mặc định. `seed-knowledge` thêm 3 bài có nhãn `[Mẫu]`, không tạo Ticket hoặc ghi đè dữ liệu cũ.

## Cấu hình

| Biến | Ý nghĩa |
|---|---|
| SECRET_KEY | Khóa ký session, cần giá trị riêng khi triển khai |
| SQLALCHEMY_DATABASE_URI | URI ưu tiên, ví dụ `mysql+pymysql://USER:PASSWORD@localhost/smart_ticket_db` |
| DATABASE_URL | URI dự phòng nếu biến trên trống |
| GROQ_API_KEY | Khóa Groq; để trống để chỉ tra cứu nội bộ |
| GROQ_MODEL | Mặc định `llama-3.3-70b-versatile`, có thể thay theo tài khoản |
| COOKIE_SECURE | `true` khi triển khai HTTPS; local HTTP dùng `false` |

`.env` được nạp từ thư mục dự án, không ghi đè biến môi trường đã đặt. `.env` không được đưa vào Git. Mật khẩu có ký tự đặc biệt trong URI phải URL-encode. Fallback MySQL local giữ như dự án gốc; không dùng tài khoản root không mật khẩu để triển khai công khai.

## AI Groq

1. Tạo API key trên [Groq Console](https://console.groq.com/keys), đặt `GROQ_API_KEY` trong `.env`, khởi động lại server.
2. Admin xuất bản bài hướng dẫn đã được kiểm tra.
3. Mở Trợ lý AI, nhập câu hỏi, chọn cho phép gửi câu hỏi và nguồn đến Groq, rồi gửi.
4. Kết quả ghi rõ **Groq** hoặc **tra cứu nội bộ**. Không có nguồn phù hợp thì không gọi model.

AI không đọc toàn bộ database, không gửi mật khẩu tài khoản, không gửi bình luận/nhật ký; nội dung Ticket chỉ xuất hiện khi người dùng chọn Ticket và nhìn thấy trong ô câu hỏi có thể sửa. Có che một số khóa/email nhưng đây không phải công cụ loại bỏ toàn bộ dữ liệu nhạy cảm. Chỉ gửi sau khi người dùng tích chọn. Phản hồi hiển thị dạng văn bản được escape; model không được cấp công cụ thực thi hay cập nhật Ticket. Tối đa 20 yêu cầu/giờ/người dùng; log chỉ lưu người dùng, Ticket liên quan, thời gian và chế độ, không lưu prompt/response.

Tham khảo API chính thức: https://console.groq.com/docs/api-reference và https://console.groq.com/docs/models.
**Chưa có API key khi bàn giao: đã test nhánh tích hợp bằng phản hồi giả lập, chưa xác nhận gọi Groq thật hoặc chất lượng câu trả lời của model.**

## Database và migration

```powershell
.\.venv\Scripts\python.exe -m flask --app run db current
.\.venv\Scripts\python.exe -m flask --app run db upgrade
.\.venv\Scripts\python.exe -m flask --app run db check
```

Sao lưu và thử trên bản sao trước khi nâng cấp database đang có dữ liệu. Database có bảng nhưng chưa có revision cần đối chiếu schema, không tự ý `stamp head`.

- `000000000001`: tạo baseline bị thiếu trước đây; các database đã có revision cũ không chạy lại baseline.
- `000000000002`: thêm timestamp thiếu, giữ nguyên cột đã tồn tại. Revision này chỉ nâng cấp; muốn quay lại cần khôi phục backup.
- `000000000003`: thêm trạng thái tài khoản, bài viết, nhật ký và metadata lượt hỏi AI. Không sửa Ticket cũ.

Bản sao lưu bàn giao riêng là dữ liệu riêng tư; không đưa lên GitHub hoặc đính kèm báo cáo công khai.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

Tests tự tạo SQLite tạm, không dùng database thật. Bao phủ migration, phân quyền, CRUD, workflow, CSRF, khóa đăng nhập, dữ liệu nhập sai, CSV, truy xuất KB và AI mock. Migration còn được kiểm tra trực tiếp trên MariaDB sạch và bản khôi phục dữ liệu thực tế; xem `docs/TEST_REPORT.md`.

## Phạm vi bàn giao

Đây là bản ứng dụng local phục vụ demo/báo cáo. Chưa tích hợp email, tệp đính kèm, SSO/MFA, giám sát SLA hoặc triển khai Internet. Tìm kiếm AI là lexical retrieval, không phải vector database, fine-tuning hay model tự huấn luyện. Bộ đếm đăng nhập sai nằm trong một tiến trình; nếu chạy nhiều tiến trình/máy cần bộ đếm chung. Chưa benchmark tải đồng thời. Nhật ký bắt đầu từ phiên bản mới, không tái tạo lịch sử cũ. Thời gian lưu/hiển thị UTC.

Tài liệu báo cáo và kịch bản demo nằm trong `docs/`.
