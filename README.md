# SmartTicket System

Ứng dụng quản lý hỗ trợ IT bằng Flask, MariaDB/MySQL (hoặc SQLite), kèm Knowledge Base và tích hợp Groq.

## Chức năng

- **User:** đăng ký/đăng nhập, đổi mật khẩu, tạo/theo dõi Ticket, bình luận, xác nhận đã khắc phục hoặc trả lại xử lý.
- **IT Support:** tiếp nhận, chuyển phiếu, nhập phương án xử lý, chờ xác nhận rồi đóng Ticket; viết bài nháp Knowledge Base.
- **Admin:** dashboard, thống kê 7 ngày, khối lượng nhân viên, xuất CSV, quản lý danh mục, tạo tài khoản/đổi vai trò/khóa tài khoản/đặt lại mật khẩu; duyệt bài viết; xem nhật ký.
- **Knowledge Base:** tìm kiếm, lọc danh mục, bản nháp/xuất bản, tạo bản nháp từ phương án Ticket; chỉ bài đã xuất bản được dùng cho trợ lý.
- **AI:** truy xuất 3 bài liên quan bằng BM25 trên từ khóa tiếng Việt bỏ dấu; gọi Groq khi có khóa và người dùng cho phép gửi câu hỏi. Không có khóa hoặc dịch vụ lỗi thì hiển thị tra cứu nội bộ có nhãn rõ ràng.

## Bản MVP ngày 06/10/2026

Đã kiểm tra trên checkout branch `feature/it-dashboard-redesign`, xuất phát từ `d28547d`.
37 test tự động đạt trên Windows/Python 3.14.7 với SQLite tạm. Không có database
MySQL thực tế hoặc API key trong checkout này; các kết quả lịch sử bên dưới không
thay thế việc kiểm tra trên máy demo.

IT/Admin mở chi tiết Ticket để phân tích bằng Groq: xác nhận gửi tiêu đề/mô tả,
nhấn Phân tích, xem category, risk_level Low/Medium/High/Critical và 2–3 bước.
Kết quả cùng model, người yêu cầu, thời gian, ticket và chế độ được lưu trong DB.
AI không tự đổi danh mục hoặc trạng thái. Khi thiếu key/lỗi provider, có thông báo
và vẫn xử lý thủ công. Chức năng hỏi đáp Knowledge Base tiếp tục hoạt động.

## Cài từ đầu hoặc trên máy khác

Python đã kiểm tra: **3.14.7**. MariaDB đã kiểm tra: **10.4.32 (XAMPP)**.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
```

Tạo SECRET_KEY bằng lệnh sau rồi đặt giá trị vào `.env`:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Đặt URI database trong `.env`. Không dùng giá trị placeholder của file mẫu. Tạo database MySQL trống trước nếu dùng MySQL. Hoặc dùng SQLite:

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
| SECRET_KEY | Khóa ký session ổn định giữa các lần chạy; nếu thiếu, dùng khóa ngẫu nhiên theo tiến trình, session sẽ hết hiệu lực khi restart |
| SQLALCHEMY_DATABASE_URI | URI ưu tiên, ví dụ `mysql+pymysql://USER:PASSWORD@localhost/smart_ticket_db` |
| DATABASE_URL | URI dự phòng nếu biến trên trống |
| GROQ_API_KEY | Khóa Groq; để trống để chỉ tra cứu nội bộ |
| GROQ_MODEL | Mặc định `openai/gpt-oss-20b`, có thể thay theo tài khoản |
| COOKIE_SECURE | `true` khi triển khai HTTPS; local HTTP dùng `false` |

`.env` được nạp từ thư mục dự án, không ghi đè biến môi trường đã đặt. `.env` không được đưa vào Git. Mật khẩu có ký tự đặc biệt trong URI phải URL-encode. Fallback MySQL local giữ như dự án gốc; không dùng tài khoản root không mật khẩu để triển khai công khai.

## AI Groq

1. Tạo API key trên [Groq Console](https://console.groq.com/keys), đặt `GROQ_API_KEY` trong `.env`, khởi động lại server.
2. Admin xuất bản bài hướng dẫn đã được kiểm tra.
3. Mở Trợ lý AI, nhập câu hỏi, chọn cho phép gửi câu hỏi và nguồn đến Groq, rồi gửi.
4. Kết quả ghi rõ **Groq** hoặc **tra cứu nội bộ**. Không có nguồn phù hợp thì không gọi model.

AI không đọc toàn bộ database, không gửi mật khẩu tài khoản, không gửi bình luận/nhật ký; nội dung Ticket chỉ xuất hiện khi người dùng chọn Ticket và nhìn thấy trong ô câu hỏi có thể sửa. Có che một số khóa/email nhưng đây không phải công cụ loại bỏ toàn bộ dữ liệu nhạy cảm. Chỉ gửi sau khi người dùng tích chọn. Phản hồi hiển thị dạng văn bản được escape; model không được cấp công cụ thực thi hay cập nhật Ticket. Tối đa 20 yêu cầu/giờ/người dùng; DB lưu metadata và kết quả trả lời/phân tích để kiểm tra lại; không lưu bản sao prompt. Chỉ nhân viên IT/Admin thấy kết quả phân tích trên Ticket. Không đưa bí mật vào câu hỏi hoặc mô tả Ticket.

Tham khảo API chính thức: https://console.groq.com/docs/api-reference và https://console.groq.com/docs/models.
**Bằng chứng lịch sử từ bản trước: đã kiểm tra kết nối Groq thực tế sau khi sửa cấu hình model và chứng chỉ HTTPS. Đây là kiểm tra khả năng kết nối, chưa phải đánh giá độ chính xác câu trả lời. Các nhánh lỗi được kiểm thử tự động bằng phản hồi giả lập.**

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
- `000000000004` (head hiện tại): thêm purpose/result/model cho AIRequest; bản ghi cũ nhận purpose=qa, result/model để trống. Giữ Ticket và lịch sử cũ.

Bản sao lưu bàn giao riêng là dữ liệu riêng tư; không đưa lên GitHub hoặc đính kèm báo cáo công khai.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

Tests tự tạo SQLite tạm, không dùng database thật. Bao phủ migration, phân quyền, CRUD, workflow, CSRF, khóa đăng nhập, dữ liệu nhập sai, CSV, truy xuất KB và AI mock. Bản trước từng kiểm tra migration trên MariaDB; migration 000000000004 hiện đã kiểm tra bằng SQLite và cần chạy trên bản sao MySQL trước demo; xem `docs/TEST_REPORT.md`.

## Phạm vi bàn giao

Đây là bản ứng dụng local phục vụ demo/báo cáo. Chưa tích hợp email, tệp đính kèm, SSO/MFA, giám sát SLA hoặc triển khai Internet. Tìm kiếm AI là lexical retrieval, không phải vector database, fine-tuning hay model tự huấn luyện. Bộ đếm đăng nhập sai nằm trong một tiến trình; nếu chạy nhiều tiến trình/máy cần bộ đếm chung. Chưa benchmark tải đồng thời. Nhật ký bắt đầu từ phiên bản mới, không tái tạo lịch sử cũ. Thời gian lưu/hiển thị UTC.

Tài liệu báo cáo và kịch bản demo nằm trong `docs/`.

## Đánh giá phục vụ đồ án

Chạy `python evaluation/run.py` để so sánh cách tìm kiếm cũ và BM25 trên dữ liệu mô phỏng. Xem [quy trình đánh giá](evaluation/README.md) và [kế hoạch hoàn thiện 3 ngày](docs/THESIS_READINESS.md). Không cần API key hoặc kết nối database.

## Bản chốt báo cáo

Xem [biên bản kiểm thử](docs/TEST_REPORT.md), [tài liệu nền](docs/REPORT_GUIDE.md) và [kịch bản demo](docs/DEMO_SCRIPT.md). Khi cập nhật máy đã có môi trường ảo, chạy `python -m pip install -r requirements-lock.txt` bằng Python của môi trường đó. Khởi động lại server sau khi cập nhật. Giữ nguyên `.env`; không thay bằng `.env.example`.
