# Kịch bản demo 10–15 phút

## Chuẩn bị

Bật MySQL/XAMPP, chạy `start.bat`, mở http://127.0.0.1:5000. Đăng nhập Admin bằng file bàn giao riêng; không chiếu mật khẩu lên màn hình báo cáo. Dùng cửa sổ trình duyệt riêng cho mỗi vai trò hoặc đăng xuất trước khi đổi tài khoản.

## Các bước

1. **Admin:** mở Tổng quan, kiểm tra thống kê, mở Người dùng & vai trò, tạo tài khoản User và IT Support dùng cho demo với mật khẩu riêng.
2. **Danh mục:** tạo danh mục “Demo - thiết bị văn phòng”, sửa mô tả.
3. **User:** tạo Ticket “Máy in không nhận lệnh”; mô tả thời điểm và triệu chứng; xem trạng thái Open.
4. **Admin:** mở Ticket, phân công nhân viên IT Support vừa tạo.
5. **IT:** mở Bàn xử lý IT, tiếp nhận; Ticket thành In Progress. Thêm bình luận và nhập phương án xử lý.
6. **User:** xem kết quả Resolved; chọn “Vẫn còn lỗi” để minh họa quay lại In Progress.
7. **IT:** bổ sung phương án và gửi lại. **User:** xác nhận “Đã khắc phục”. **IT:** đóng Ticket; kiểm tra Closed, timestamp và lịch sử.
8. **Knowledge Base:** IT tạo bài nháp từ phương án. Admin chỉnh sửa bỏ dữ liệu riêng và xuất bản. User tìm và đọc bài mới.
9. **Trợ lý:** hỏi “Máy in không nhận lệnh”. Khi chưa có khóa, chỉ ra nhãn tra cứu nội bộ và nguồn bài viết. Không trình bày đây là kết quả Groq. Nếu đã thêm khóa riêng và khởi động lại server, chọn cho phép gửi rồi kiểm thử thêm.
10. **Quản trị:** xem nhật ký, xuất CSV, kiểm tra thống kê. Minh họa không xóa được danh mục đang được dùng.

## Ảnh nên chụp cho báo cáo

Đăng nhập; dashboard Admin; danh sách Ticket; chi tiết In Progress; User xác nhận; bài KB; trợ lý và nguồn; trang quản lý người dùng; nhật ký. Ghi “dữ liệu demo” khi dùng tài khoản/Ticket minh họa. Che thông tin riêng của dữ liệu cũ.

## Sau demo

Giữ Ticket demo để thể hiện nhật ký hoặc sao lưu trước khi dọn dữ liệu. Không xóa database thật. Đổi mật khẩu Admin được bàn giao và giữ file thông tin đăng nhập ở nơi riêng.
