# Hướng dẫn demo/người dùng ngắn

1. Migrate database, tạo Admin bằng CLI, khởi động server theo README. Admin tạo hai tài khoản IT và một User, thêm Category.
2. User tạo ticket mô tả Wi-Fi không kết nối; kiểm tra ticket xuất hiện trên User dashboard.
3. IT nhận ticket. Mở chi tiết, tích đồng ý gửi dữ liệu tới Groq và Phân tích. Xem category/risk/2–3 bước. Thiếu key thì chỉ thông báo, không cản workflow.
4. IT chuyển ticket cho IT thứ hai. IT cũ thử resolve phải bị chặn. IT mới nhập resolution_note và hoàn tất.
5. User chọn Vẫn còn lỗi: ticket trở về In Progress. IT xử lý lại và gửi kết quả. User chọn Đã khắc phục; IT đóng.
6. IT tạo bài nháp từ kết quả xử lý; sửa bỏ thông tin riêng tư. Admin duyệt/xuất bản. User tìm kiếm KB và thử hỏi đáp AI có nguồn.
7. Admin xem dashboard, tất cả Ticket trong IT dashboard tab All, xuất CSV và nhật ký. Tạo/sửa/xóa Category trống; thử khóa User. Tài khoản có ticket chưa đóng phải chuyển ticket trước khi khóa/hạ quyền.

AI là đề xuất, IT chịu trách nhiệm kiểm chứng. Không nhập bí mật vào ticket/câu hỏi.
Ngày giờ hiển thị UTC. Logout dùng nút trên UI. Không có mật khẩu/tài khoản mẫu mặc định.
Giữ nguyên .env khi cập nhật; thêm GROQ_API_KEY thủ công và restart để dùng Groq.
