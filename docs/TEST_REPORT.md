# Biên bản kiểm thử và bàn giao

Ngày thực hiện: 25/09/2026. Phạm vi: phiên bản local SmartTicket System.

## Môi trường

- Windows; Python 3.14.7; dependencies trong `requirements-lock.txt`.
- SQLite tạm cho kiểm thử tự động, không kết nối dữ liệu thật.
- MariaDB 10.4.32 của XAMPP cho kiểm tra migration và database thực tế.

## Kết quả

| Nhóm | Bằng chứng | Kết quả |
|---|---|---|
| Tự động | `python -m unittest discover -s tests -v` | 27 test đạt |
| Cú pháp | Compile toàn bộ app/tests/config/launcher | Đạt |
| Dependencies | `pip check` | Không có dependency hỏng |
| Migration mới | MariaDB riêng, schema trống → revision 000000000003 | Đạt; so sánh metadata không có chênh lệch |
| Migration dữ liệu cũ | Khôi phục backup vào MariaDB riêng rồi nâng cấp | Đạt; schema khớp model |
| Database thật | Nâng cấp smart_ticket_db → 000000000003 | Đạt |
| Giữ dữ liệu gốc | Đối chiếu SHA-256 nội dung và ID các bản ghi cũ trước/sau | Giữ nguyên 5 users, 3 categories, 6 tickets, 3 comments |
| Trang/quyền trên DB thật | 67 lượt GET qua Flask test client, tất cả vai trò, gồm các trường hợp 403 dự kiến | Đạt |
| AI | Mock thành công, timeout, response sai cấu trúc, không khóa, không nguồn, không đồng ý gửi, vượt quota | Đạt |
| Groq trực tuyến | Không có API key | Chưa thực hiện |
| Giao diện trực quan | Công cụ browser báo lỗi phiên kết nối | Chưa xác nhận bằng ảnh; đã kiểm tra render HTML |

## Các ca chính trong 27 test

Migration database trống/cũ/có timestamp/một phần timestamp; downgrade migration lịch sử; vòng đời Ticket và HTML cho từng vai trò/trạng thái; trang Admin; giới hạn vai trò; Category CRUD và ràng buộc; tạo/khóa tài khoản và bảo vệ Admin; không khóa người còn công việc; nháp/duyệt/tìm KB; Ticket → bài nháp; AI fallback/provider mock/timeout/HTML escape/nguồn/quota/response lỗi; kiểm tra input; xác nhận chưa khắc phục; CSRF/logout; đăng ký không tự nâng quyền; khóa đăng nhập sai; CSV formula; đổi mật khẩu.

Test chạy tự động không chứng minh hệ thống không có mọi lỗi, không đo tải lớn, không kiểm thử nhiều trình duyệt và không đánh giá chất lượng mô hình thực.

## Thay đổi có chủ đích vào database thật

Thêm cột `users.enabled` (mặc định hoạt động), các bảng `knowledge_articles`, `audit_events`, `ai_requests`. Tạo riêng Admin `report_admin` với mật khẩu ngẫu nhiên bàn giao trong file local. Thêm 3 bài `[Mẫu]` để demo. Không đổi mật khẩu/vai trò của các tài khoản cũ; không tạo hoặc sửa Ticket/bình luận cũ.

Backup trước nâng cấp được lưu riêng bên ngoài repo/ZIP. Backup và file mật khẩu không được đưa vào báo cáo công khai.

## Khi thêm khóa Groq

Chạy lại tối thiểu: câu hỏi có nguồn, không có nguồn, khóa sai, quota nhà cung cấp, câu hỏi chứa dữ liệu cần che, prompt injection trong bài nháp/xuất bản, kiểm tra độ trung thực với nguồn. Ghi số ca, câu hỏi và tiêu chí chấm trước khi công bố độ chính xác.
